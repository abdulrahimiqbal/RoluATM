#!/bin/bash
"""
RoluATM Raspberry Pi Deployment Test Script
Tests all components on the actual Raspberry Pi
"""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Logging
log_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

log_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

echo -e "${BLUE}🍓 RoluATM Raspberry Pi Deployment Test${NC}"
echo "=============================================="

# Test 1: System Requirements
echo -e "\n📋 Testing System Requirements..."

# Check OS
if grep -q "Raspberry Pi" /proc/cpuinfo; then
    log_pass "Running on Raspberry Pi"
else
    log_warning "Not running on Raspberry Pi (testing on other system)"
fi

# Check Node.js
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    log_pass "Node.js installed: $NODE_VERSION"
else
    log_fail "Node.js not installed"
fi

# Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    log_pass "Python3 installed: $PYTHON_VERSION"
else
    log_fail "Python3 not installed"
fi

# Check PostgreSQL
if command -v psql >/dev/null 2>&1; then
    log_pass "PostgreSQL client installed"
else
    log_fail "PostgreSQL client not installed"
fi

# Test 2: Project Files
echo -e "\n📁 Testing Project Structure..."

PROJECT_FILES=(
    "package.json"
    "requirements.txt"
    "env.template"
    "server/app.py"
    "client/src/App.tsx"
    "start-kiosk.sh"
)

for file in "${PROJECT_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_pass "File exists: $file"
    else
        log_fail "Missing file: $file"
    fi
done

# Test 3: Dependencies
echo -e "\n📦 Testing Dependencies..."

# Test npm dependencies
if [ -f "package.json" ] && [ -d "node_modules" ]; then
    log_pass "Node.js dependencies installed"
else
    log_fail "Node.js dependencies missing - run 'npm install'"
fi

# Test Python virtual environment
if [ -d "venv" ]; then
    log_pass "Python virtual environment exists"
    
    # Activate and test
    source venv/bin/activate
    if python -c "import flask" 2>/dev/null; then
        log_pass "Flask installed in virtual environment"
    else
        log_fail "Flask not installed - run 'pip install -r requirements.txt'"
    fi
    deactivate
else
    log_fail "Python virtual environment missing - run 'python3 -m venv venv'"
fi

# Test 4: Environment Configuration
echo -e "\n🔧 Testing Environment Configuration..."

if [ -f ".env.local" ]; then
    log_pass "Environment file exists: .env.local"
    
    # Check for required variables
    ENV_VARS=(
        "VITE_WORLD_APP_ID"
        "WORLD_CLIENT_SECRET"
        "DATABASE_URL"
        "TFLEX_PORT"
    )
    
    for var in "${ENV_VARS[@]}"; do
        if grep -q "^$var=" .env.local; then
            VALUE=$(grep "^$var=" .env.local | cut -d'=' -f2)
            if [ -n "$VALUE" ] && [ "$VALUE" != "your_app_id_here" ] && [ "$VALUE" != "your_secret_here" ]; then
                log_pass "Environment variable configured: $var"
            else
                log_warning "Environment variable needs configuration: $var"
            fi
        else
            log_fail "Missing environment variable: $var"
        fi
    done
else
    log_warning "No .env.local file - will be created from template"
fi

# Test 5: Hardware Detection
echo -e "\n🔌 Testing Hardware..."

# Check for touch screen
if xinput list 2>/dev/null | grep -i touch >/dev/null; then
    log_pass "Touch screen detected"
else
    log_warning "Touch screen not detected (may need calibration)"
fi

# Check for serial ports (T-Flex)
SERIAL_PORTS=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true)
if [ -n "$SERIAL_PORTS" ]; then
    log_pass "Serial ports available: $SERIAL_PORTS"
else
    log_warning "No serial ports detected (T-Flex not connected?)"
fi

# Check user permissions
if groups | grep -q dialout; then
    log_pass "User has serial port permissions (dialout group)"
else
    log_warning "User needs serial permissions - run 'sudo usermod -a -G dialout \$USER'"
fi

# Test 6: Network Configuration
echo -e "\n🌐 Testing Network..."

# Check internet connectivity
if ping -c 1 google.com >/dev/null 2>&1; then
    log_pass "Internet connectivity available"
else
    log_fail "No internet connectivity"
fi

# Check if ports are available
if ! netstat -tlnp 2>/dev/null | grep -q :3000; then
    log_pass "Port 3000 available for frontend"
else
    log_warning "Port 3000 in use"
fi

if ! netstat -tlnp 2>/dev/null | grep -q :8000; then
    log_pass "Port 8000 available for backend"
else
    log_warning "Port 8000 in use"
fi

# Test 7: Display Configuration
echo -e "\n🖥️ Testing Display Configuration..."

if [ -n "$DISPLAY" ]; then
    log_pass "Display environment variable set: $DISPLAY"
else
    log_warning "No DISPLAY variable (headless mode?)"
fi

# Check for Chromium
if command -v chromium-browser >/dev/null 2>&1; then
    log_pass "Chromium browser installed"
else
    log_fail "Chromium browser not installed - run 'sudo apt-get install chromium-browser'"
fi

# Test 8: Quick Function Test
echo -e "\n🧪 Testing Basic Functionality..."

# Test backend can start
echo "Testing backend startup..."
if [ -d "venv" ]; then
    source venv/bin/activate
    timeout 10 python server/app.py &>/dev/null &
    BACKEND_PID=$!
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_pass "Backend can start"
        kill $BACKEND_PID 2>/dev/null
    else
        log_fail "Backend failed to start"
    fi
    deactivate
else
    log_fail "Cannot test backend - no virtual environment"
fi

# Test frontend can build
echo "Testing frontend build..."
if npm run build >/dev/null 2>&1; then
    log_pass "Frontend builds successfully"
else
    log_fail "Frontend build failed"
fi

# Summary
echo -e "\n" + "=" * 50
echo -e "${BLUE}Test Summary:${NC}"
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Your Pi is ready for RoluATM deployment.${NC}"
    echo -e "${BLUE}To start the kiosk, run: ./start-kiosk.sh${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Please fix the issues above before deploying.${NC}"
    echo -e "${BLUE}See RASPBERRY_PI_SETUP.md for detailed setup instructions.${NC}"
fi

echo -e "\n${BLUE}📋 Quick Start Commands:${NC}"
echo "1. Install dependencies: npm install && pip install -r requirements.txt"
echo "2. Configure environment: cp env.template .env.local && nano .env.local"
echo "3. Start kiosk: ./start-kiosk.sh" 