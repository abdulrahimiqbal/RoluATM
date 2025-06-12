#!/usr/bin/env python3
"""
RoluATM Resilient Dispenser Service
Polls cloud API for dispense jobs and executes them with retry logic
Designed to survive Pi reboots and network issues
"""

import os
import sys
import json
import uuid
import time
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Import existing T-Flex dispenser class
try:
    from pi_backend import TFlexDispenser
except ImportError:
    # Fallback if running standalone
    class TFlexDispenser:
        def __init__(self):
            self.mock_mode = True
            
        def dispense_quarters(self, count):
            print(f"🪙 Mock dispensing {count} quarters...")
            time.sleep(2)  # Simulate dispensing time
            return True
            
        def get_status(self):
            return {"status": "mock", "quarters_available": 1000}

# Configuration
API_BASE = os.environ.get('VERCEL_API_URL', 'https://rolu-api.vercel.app/api/v2')
KIOSK_ID_FILE = Path.home() / '.rolu_kiosk_id'
LOG_FILE = Path.home() / 'dispenser_service.log'
POLL_INTERVAL = 2  # seconds
ERROR_BACKOFF = 5  # seconds
MAX_CONSECUTIVE_ERRORS = 10

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ResilientDispenserService:
    """Resilient dispenser service that handles job polling and execution"""
    
    def __init__(self):
        self.kiosk_id = self.get_or_generate_kiosk_id()
        self.api_base = API_BASE
        self.tflex = TFlexDispenser()
        self.last_job_id = None
        self.consecutive_errors = 0
        self.session = requests.Session()
        
        # Set session defaults
        self.session.headers.update({
            'x-kiosk-id': self.kiosk_id,
            'Content-Type': 'application/json'
        })
        
        logger.info(f"🚀 RoluATM Dispenser Service starting...")
        logger.info(f"📍 Kiosk ID: {self.kiosk_id}")
        logger.info(f"🌐 API Base: {self.api_base}")
        logger.info(f"🔧 T-Flex Mode: {'Hardware' if not self.tflex.mock_mode else 'Mock'}")
        
    def get_or_generate_kiosk_id(self):
        """Get persistent kiosk ID that survives reboots"""
        try:
            if KIOSK_ID_FILE.exists():
                with open(KIOSK_ID_FILE, 'r') as f:
                    kiosk_id = f.read().strip()
                    if kiosk_id:
                        return kiosk_id
            
            # Generate new kiosk ID
            kiosk_id = str(uuid.uuid4())
            KIOSK_ID_FILE.parent.mkdir(exist_ok=True)
            with open(KIOSK_ID_FILE, 'w') as f:
                f.write(kiosk_id)
            
            logger.info(f"Generated new kiosk ID: {kiosk_id}")
            return kiosk_id
            
        except Exception as e:
            logger.error(f"Failed to get/generate kiosk ID: {e}")
            # Fallback to temporary ID
            return str(uuid.uuid4())
    
    def run_forever(self):
        """Main service loop - polls for jobs and executes them"""
        logger.info("🔄 Starting main service loop...")
        
        while True:
            try:
                job = self.get_next_job()
                
                if job:
                    self.process_job(job)
                    self.consecutive_errors = 0  # Reset error counter on success
                else:
                    # No job available, wait before next poll
                    time.sleep(POLL_INTERVAL)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Service stopped by user")
                break
            except Exception as e:
                self.consecutive_errors += 1
                logger.error(f"Service error #{self.consecutive_errors}: {e}")
                
                if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.error(f"Too many consecutive errors ({MAX_CONSECUTIVE_ERRORS}), restarting...")
                    self.consecutive_errors = 0
                    time.sleep(30)  # Longer backoff before restart
                else:
                    time.sleep(ERROR_BACKOFF)
    
    def get_next_job(self):
        """Poll for pending dispense jobs"""
        try:
            response = self.session.get(
                f"{self.api_base}/jobs/pending",
                timeout=10
            )
            
            if response.status_code == 200:
                job = response.json()
                if job:
                    logger.info(f"📥 Received job: {job['id']} ({job['quarters']} quarters)")
                return job
            elif response.status_code == 400:
                logger.error(f"Bad request: {response.text}")
            else:
                logger.warning(f"Unexpected response: {response.status_code}")
                
            return None
            
        except requests.exceptions.Timeout:
            logger.warning("Request timeout while polling for jobs")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error while polling for jobs")
            return None
        except Exception as e:
            logger.error(f"Error polling for jobs: {e}")
            return None
    
    def process_job(self, job):
        """Execute dispense job with comprehensive error handling"""
        job_id = job['id']
        quarters = job['quarters']
        
        # Duplicate job protection
        if job_id == self.last_job_id:
            logger.warning(f"Skipping duplicate job: {job_id}")
            return
            
        self.last_job_id = job_id
        
        logger.info(f"🎯 Processing job {job_id}: dispensing {quarters} quarters")
        
        try:
            # Pre-dispense checks
            tflex_status = self.tflex.get_status()
            if tflex_status.get('status') == 'error':
                raise Exception(f"T-Flex hardware error: {tflex_status.get('error', 'Unknown')}")
            
            # Execute dispensing
            start_time = time.time()
            success = self.tflex.dispense_quarters(quarters)
            dispense_time = time.time() - start_time
            
            if success:
                logger.info(f"✅ Successfully dispensed {quarters} quarters in {dispense_time:.2f}s")
                self.report_job_result(job_id, True)
            else:
                logger.error(f"❌ Failed to dispense quarters")
                self.report_job_result(job_id, False, "Dispenser returned failure")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Dispense error for job {job_id}: {error_msg}")
            self.report_job_result(job_id, False, error_msg)
    
    def report_job_result(self, job_id, success, error=None):
        """Report job completion status to cloud API"""
        try:
            payload = {
                "success": success,
                "kioskId": self.kiosk_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if error:
                payload["error"] = error
            
            response = self.session.post(
                f"{self.api_base}/jobs/{job_id}/complete",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📤 Job result reported: {result.get('status', 'unknown')}")
                
                if result.get('status') == 'retry':
                    logger.info(f"🔄 Job will be retried: {result.get('message', '')}")
                    
            else:
                logger.error(f"Failed to report job result: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error reporting job result: {e}")
            # Don't raise - we'll try again on next poll if needed
    
    def health_check(self):
        """Perform health check and return status"""
        try:
            tflex_status = self.tflex.get_status()
            
            return {
                "kiosk_id": self.kiosk_id,
                "tflex_status": tflex_status,
                "api_base": self.api_base,
                "consecutive_errors": self.consecutive_errors,
                "last_job_id": self.last_job_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

def main():
    """Main entry point"""
    try:
        service = ResilientDispenserService()
        
        # Print startup info
        health = service.health_check()
        logger.info(f"🏥 Health check: {json.dumps(health, indent=2)}")
        
        # Start main loop
        service.run_forever()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 