#!/usr/bin/env node

/**
 * WorldCash Phase 2 Test Script
 * Tests World ID integration, database connectivity, and backend functionality
 */

const fs = require('fs');
const https = require('https');

console.log('🧪 Testing WorldCash Phase 2 Setup...\n');

// Test 1: Environment Variables
console.log('🔧 Checking Phase 2 environment variables...');
let envOk = true;
try {
  const envContent = fs.readFileSync('.env.local', 'utf8');
  const requiredEnvVars = [
    'VITE_WORLD_APP_ID',
    'WORLD_CLIENT_SECRET', 
    'DATABASE_URL',
    'VITE_API_URL'
  ];
  
  requiredEnvVars.forEach(envVar => {
    if (envContent.includes(`${envVar}=`) && !envContent.includes(`${envVar}=your_`)) {
      console.log(`  ✅ ${envVar} configured`);
    } else {
      console.log(`  ❌ ${envVar} missing or has placeholder value`);
      envOk = false;
    }
  });
} catch (e) {
  console.log('  ❌ Could not read .env.local');
  envOk = false;
}

// Test 2: World ID App Configuration
console.log('\n🌍 Testing World ID configuration...');
try {
  const envContent = fs.readFileSync('.env.local', 'utf8');
  const appIdMatch = envContent.match(/VITE_WORLD_APP_ID=(.+)/);
  if (appIdMatch && appIdMatch[1] && !appIdMatch[1].includes('your_')) {
    console.log('  ✅ World App ID looks valid');
    // Could add API test here later
  } else {
    console.log('  ❌ World App ID not configured');
  }
} catch (e) {
  console.log('  ❌ Could not check World ID config');
}

// Test 3: Database Connection Test
console.log('\n🗄️  Testing database connectivity...');
try {
  const envContent = fs.readFileSync('.env.local', 'utf8');
  const dbUrlMatch = envContent.match(/DATABASE_URL=(.+)/);
  if (dbUrlMatch && dbUrlMatch[1] && dbUrlMatch[1].includes('neon.tech')) {
    console.log('  ✅ Neon database URL configured');
    console.log('  ⚠️  Database connection test requires backend running');
  } else {
    console.log('  ❌ Neon database URL not configured');
  }
} catch (e) {
  console.log('  ❌ Could not check database config');
}

// Test 4: Python Backend Dependencies
console.log('\n🐍 Checking Python backend setup...');
if (fs.existsSync('venv/bin/activate')) {
  console.log('  ✅ Python virtual environment exists');
  console.log('  ⚠️  Run backend test: source venv/bin/activate && python src/backend/app.py');
} else {
  console.log('  ❌ Python virtual environment not found');
  console.log('  💡 Create with: python3 -m venv venv');
}

// Test 5: MiniKit Integration Files
console.log('\n📱 Checking MiniKit integration...');
const miniKitFiles = [
  'client/src/hooks/useWorldId.ts',
  'client/src/App.tsx',
  'client/src/vite-env.d.ts'
];

miniKitFiles.forEach(file => {
  if (fs.existsSync(file)) {
    const content = fs.readFileSync(file, 'utf8');
    if (content.includes('@worldcoin/minikit-react')) {
      console.log(`  ✅ ${file} has MiniKit imports`);
    } else {
      console.log(`  ⚠️  ${file} exists but may need MiniKit integration`);
    }
  } else {
    console.log(`  ❌ ${file} missing`);
  }
});

// Test 6: Frontend Server Test
console.log('\n🖥️  Testing frontend server...');
const http = require('http');
const testUrl = 'http://localhost:3000';

const req = http.get(testUrl, (res) => {
  if (res.statusCode === 200) {
    console.log('  ✅ Frontend server responding on port 3000');
  } else {
    console.log(`  ⚠️  Frontend server returned status ${res.statusCode}`);
  }
}).on('error', (err) => {
  console.log('  ❌ Frontend server not running - start with: npx vite --port 3000');
});

// Final Results
setTimeout(() => {
  console.log('\n' + '='.repeat(60));
  console.log('📋 Phase 2 Quick Start Commands:');
  console.log('');
  console.log('1. Create Neon database:');
  console.log('   Visit: https://console.neon.tech');
  console.log('   Copy DATABASE_URL to .env.local');
  console.log('');
  console.log('2. Get World ID credentials:');
  console.log('   Visit: https://developer.worldcoin.org');
  console.log('   Create app and copy credentials to .env.local');
  console.log('');
  console.log('3. Setup Python backend:');
  console.log('   brew install postgresql  # for psycopg2');
  console.log('   source venv/bin/activate');
  console.log('   pip install -r requirements.txt');
  console.log('');
  console.log('4. Test everything:');
  console.log('   npx vite --port 3000  # frontend');
  console.log('   python src/backend/app.py  # backend (separate terminal)');
  console.log('');
  console.log('='.repeat(60));
}, 1000); 