"""
RoluATM Backend Settings
Configuration management for environment variables and defaults
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class Settings:
    """Application settings loaded from environment variables"""
    
    # Hardware settings
    TFLEX_PORT: str = os.getenv("TFLEX_PORT", "/dev/ttyACM0")
    
    # API endpoints
    WORLD_API_URL: str = os.getenv("WORLD_API_URL", "https://id.worldcoin.org/api/v1")
    WALLET_API_URL: str = os.getenv("WALLET_API_URL", "https://wallet.example.com")
    FX_URL: str = os.getenv("FX_URL", "https://api.kraken.com/0/public/Ticker?pair=WBTCUSD")
    
    # Currency settings
    FIAT_DENOM: str = os.getenv("FIAT_DENOM", "USD")
    COIN_VALUE: float = float(os.getenv("COIN_VALUE", "0.25"))  # Quarter value
    
    # Application settings
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Security settings
    MAX_WITHDRAWAL_USD: float = float(os.getenv("MAX_WITHDRAWAL_USD", "500.00"))
    MIN_WITHDRAWAL_USD: float = float(os.getenv("MIN_WITHDRAWAL_USD", "1.00"))
    
    # Timeout settings
    WORLD_ID_TIMEOUT: int = int(os.getenv("WORLD_ID_TIMEOUT", "30"))
    WALLET_TIMEOUT: int = int(os.getenv("WALLET_TIMEOUT", "10"))
    DISPENSE_TIMEOUT: int = int(os.getenv("DISPENSE_TIMEOUT", "30"))
    
    def __post_init__(self):
        """Validate settings after initialization"""
        if self.COIN_VALUE <= 0:
            raise ValueError("COIN_VALUE must be positive")
        
        if self.MAX_WITHDRAWAL_USD <= self.MIN_WITHDRAWAL_USD:
            raise ValueError("MAX_WITHDRAWAL_USD must be greater than MIN_WITHDRAWAL_USD")
        
        if not self.WORLD_API_URL.startswith(("http://", "https://")):
            raise ValueError("WORLD_API_URL must be a valid HTTP(S) URL")
        
        if not self.WALLET_API_URL.startswith(("http://", "https://")):
            raise ValueError("WALLET_API_URL must be a valid HTTP(S) URL")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEV_MODE
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        key_env_vars = [
            f"{service.upper()}_API_KEY",
            f"{service.upper()}_KEY",
            f"API_KEY_{service.upper()}",
            "API_KEY"
        ]
        
        for env_var in key_env_vars:
            key = os.getenv(env_var)
            if key:
                return key
        
        return None
    
    def validate_environment(self) -> list[str]:
        """Validate required environment variables and return any errors"""
        errors = []
        
        # Check critical settings in production
        if self.is_production:
            if self.WORLD_API_URL == "https://id.worldcoin.org/api/v1":
                if not self.get_api_key("worldcoin"):
                    errors.append("World ID API key not configured for production")
            
            if self.WALLET_API_URL == "https://wallet.example.com":
                errors.append("WALLET_API_URL not configured for production")
            
            # Check hardware device exists
            if not os.path.exists(self.TFLEX_PORT):
                errors.append(f"T-Flex device not found at {self.TFLEX_PORT}")
        
        return errors
