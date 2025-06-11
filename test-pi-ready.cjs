#!/usr/bin/env node

/**
 * RoluATM Raspberry Pi Deployment Readiness Check
 * Validates that all components are ready for Pi deployment
 */

const fs = require('fs');
const path = require('path');

console.log('🍓 RoluATM Raspberry Pi Deployment Readiness Check\n');

let allChecks = true;

// Required files for Pi deployment
const requiredFiles = [
  'package.json',
  'requirements.txt',
  'env.template',
  'client/src/App.tsx',
  'server/app.py',
  'Dockerfile.frontend',
  'Dockerfile.backend',
  'vercel.json'
];

// Required directories
const requiredDirs = [
  'client/src',
  'server',
  'shared'
];

function checkExists(itemPath, type = 'file') {
  const exists = fs.existsSync(itemPath);
  const icon = exists ? '✅' : '❌';
  console.log(`${icon} ${type}: ${itemPath}`);
  if (!exists) allChecks = false;
  return exists;
}

function checkPackageJson() {
  console.log('\n📦 Checking package.json dependencies...');
  
  try {
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    const requiredDeps = [
      '@worldcoin/minikit-js',
      'react',
      'vite',
      '@tanstack/react-query'
    ];
    
    requiredDeps.forEach(dep => {
      const hasMainDep = pkg.dependencies && pkg.dependencies[dep];
      const hasDevDep = pkg.devDependencies && pkg.devDependencies[dep];
      const exists = hasMainDep || hasDevDep;
      const icon = exists ? '✅' : '❌';
      console.log(`${icon} ${dep}: ${exists ? 'installed' : 'missing'}`);
      if (!exists) allChecks = false;
    });
    
    // Check scripts
    console.log('\n📜 Checking npm scripts...');
    const requiredScripts = ['dev', 'build'];
    requiredScripts.forEach(script => {
      const exists = pkg.scripts && pkg.scripts[script];
      const icon = exists ? '✅' : '❌';
      console.log(`${icon} npm run ${script}: ${exists ? 'available' : 'missing'}`);
      if (!exists) allChecks = false;
    });
    
  } catch (error) {
    console.log('❌ Error reading package.json:', error.message);
    allChecks = false;
  }
}

function checkRequirementsTxt() {
  console.log('\n🐍 Checking requirements.txt...');
  
  try {
    const content = fs.readFileSync('requirements.txt', 'utf8');
    const requiredPackages = [
      'Flask',
      'requests',
      'pyserial',
      'psycopg2-binary'
    ];
    
    requiredPackages.forEach(pkg => {
      const exists = content.includes(pkg);
      const icon = exists ? '✅' : '❌';
      console.log(`${icon} ${pkg}: ${exists ? 'listed' : 'missing'}`);
      if (!exists) allChecks = false;
    });
    
  } catch (error) {
    console.log('❌ Error reading requirements.txt:', error.message);
    allChecks = false;
  }
}

function checkEnvironment() {
  console.log('\n🔧 Checking environment configuration...');
  
  if (checkExists('env.template')) {
    try {
      const content = fs.readFileSync('env.template', 'utf8');
      const requiredVars = [
        'VITE_WORLD_APP_ID',
        'WORLD_CLIENT_SECRET',
        'DATABASE_URL',
        'TFLEX_PORT',
        'KIOSK_MODE'
      ];
      
      requiredVars.forEach(envVar => {
        const exists = content.includes(envVar);
        const icon = exists ? '✅' : '❌';
        console.log(`${icon} ${envVar}: ${exists ? 'in template' : 'missing'}`);
        if (!exists) allChecks = false;
      });
      
    } catch (error) {
      console.log('❌ Error reading env.template:', error.message);
      allChecks = false;
    }
  }
}

function checkWorldIdSetup() {
  console.log('\n🌍 Checking World ID integration...');
  
  // Check MiniKit provider in App.tsx
  try {
    const appContent = fs.readFileSync('client/src/App.tsx', 'utf8');
    const hasMiniKitProvider = appContent.includes('MiniKitProvider');
    const hasWorldcoinImport = appContent.includes('@worldcoin/minikit-js');
    
    const icon1 = hasMiniKitProvider ? '✅' : '❌';
    const icon2 = hasWorldcoinImport ? '✅' : '❌';
    
    console.log(`${icon1} MiniKitProvider: ${hasMiniKitProvider ? 'configured' : 'missing'}`);
    console.log(`${icon2} Worldcoin import: ${hasWorldcoinImport ? 'present' : 'missing'}`);
    
    if (!hasMiniKitProvider || !hasWorldcoinImport) allChecks = false;
    
  } catch (error) {
    console.log('❌ Error checking App.tsx:', error.message);
    allChecks = false;
  }
}

function checkDeploymentFiles() {
  console.log('\n🚀 Checking deployment files...');
  
  const deploymentFiles = [
    'Dockerfile.frontend',
    'Dockerfile.backend', 
    'vercel.json'
  ];
  
  deploymentFiles.forEach(file => {
    checkExists(file);
  });
}

function main() {
  console.log('📋 Checking required files...');
  requiredFiles.forEach(file => checkExists(file));
  
  console.log('\n📁 Checking required directories...');
  requiredDirs.forEach(dir => checkExists(dir, 'directory'));
  
  checkPackageJson();
  checkRequirementsTxt();
  checkEnvironment();
  checkWorldIdSetup();
  checkDeploymentFiles();
  
  console.log('\n' + '='.repeat(60));
  
  if (allChecks) {
    console.log('🎉 All checks passed! Your project is ready for Raspberry Pi deployment.');
    console.log('\n📋 Next steps:');
    console.log('1. Follow the RASPBERRY_PI_SETUP.md guide');
    console.log('2. Set up your World ID developer account');
    console.log('3. Configure your T-Flex coin dispenser');
    console.log('4. Test on your Raspberry Pi');
  } else {
    console.log('⚠️  Some checks failed. Please fix the issues above before deploying to Pi.');
    console.log('\n🔧 Common fixes:');
    console.log('- Run: npm install');
    console.log('- Ensure all required files are present');
    console.log('- Check that MiniKit is properly configured');
  }
  
  console.log('\n📖 See RASPBERRY_PI_SETUP.md for detailed deployment instructions.');
}

main(); 