const fs = require('fs');
const path = require('path');

// Ensure build directory exists
if (!fs.existsSync('build')) {
  console.error('Build directory does not exist. Run "npm run build" first.');
  process.exit(1);
}

// Copy main.js to build directory
try {
  fs.copyFileSync(
    path.join('src', 'main.js'),
    path.join('build', 'electron.js')
  );
  console.log('✓ Copied main.js to build/electron.js');
} catch (error) {
  console.error('Error copying main.js:', error.message);
  process.exit(1);
}

// Copy preload.js to build directory
try {
  fs.copyFileSync(
    path.join('src', 'preload.js'),
    path.join('build', 'preload.js')
  );
  console.log('✓ Copied preload.js to build/preload.js');
} catch (error) {
  console.error('Error copying preload.js:', error.message);
  process.exit(1);
}

console.log('✓ Electron build preparation complete');