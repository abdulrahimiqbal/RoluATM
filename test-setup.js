#!/usr/bin/env node

/**
 * WorldCash Setup Test Script
 * Run this to verify your setup before `npm run dev`
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing WorldCash Setup...\n');

// Test 1: Check if required files exist
const requiredFiles = [
  'package.json',
  'requirements.txt',
  'env.template',
  'client/src/App.tsx',
  'client/src/hooks/useWorldId.ts',
  'client/src/vite-env.d.ts',
  'Dockerfile.frontend',
  'Dockerfile.backend',
  'vercel.json'
];

let filesOk = true;
console.log('📁 Checking required files...');
requiredFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`  ✅ ${file}`);
  } else {
    console.log(`  ❌ ${file} - MISSING!`);
    filesOk = false;
  }
});

// Test 2: Check package.json dependencies
console.log('\n📦 Checking key dependencies...');
try {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredDeps = [
    '@worldcoin/minikit-react',
    '@tanstack/react-query',
    'wouter',
    'react',
    'vite'
  ];
  
  requiredDeps.forEach(dep => {
    if (packageJson.dependencies[dep] || packageJson.devDependencies[dep]) {
      console.log(`  ✅ ${dep}`);
    } else {
      console.log(`  ❌ ${dep} - MISSING!`);
      filesOk = false;
    }
  });
} catch (e) {
  console.log('  ❌ Could not read package.json');
  filesOk = false;
}

// Test 3: Check if .env.local exists
console.log('\n🔧 Checking environment setup...');
if (fs.existsSync('.env.local')) {
  console.log('  ✅ .env.local exists');
  try {
    const envContent = fs.readFileSync('.env.local', 'utf8');
    if (envContent.includes('VITE_WORLD_APP_ID')) {
      console.log('  ✅ VITE_WORLD_APP_ID configured');
    } else {
      console.log('  ⚠️  VITE_WORLD_APP_ID not found in .env.local');
    }
  } catch (e) {
    console.log('  ❌ Could not read .env.local');
  }
} else {
  console.log('  ⚠️  .env.local not found - copy from env.template');
}

// Test 4: Check node_modules
console.log('\n📂 Checking installation...');
if (fs.existsSync('node_modules')) {
  console.log('  ✅ node_modules exists');
} else {
  console.log('  ❌ node_modules missing - run `npm install`');
  filesOk = false;
}

// Final result
console.log('\n' + '='.repeat(50));
if (filesOk) {
  console.log('🎉 Setup looks good! Try running:');
  console.log('   npm run dev');
} else {
  console.log('❌ Setup has issues. Please fix the above problems first.');
  console.log('\n📋 Quick fix commands:');
  console.log('   npm install');
  console.log('   cp env.template .env.local');
  console.log('   # Edit .env.local with your World ID credentials');
}
console.log('='.repeat(50)); 