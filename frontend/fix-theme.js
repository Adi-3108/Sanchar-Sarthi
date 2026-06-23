const fs = require('fs');
const path = require('path');

const dirs = [
  path.join(__dirname, 'components/recommendations'),
  path.join(__dirname, 'components/reports')
];

const replacements = [
  { pattern: /bg-cyan-300(?:\/\d+)?/g, replacement: 'bg-blue-600' },
  { pattern: /border-cyan-300(?:\/\d+)?/g, replacement: 'border-blue-600' },
  { pattern: /hover:bg-cyan-[23]00(?:\/\d+)?/g, replacement: 'hover:bg-blue-500' },
  { pattern: /hover:border-cyan-[23]00(?:\/\d+)?/g, replacement: 'hover:border-blue-500' },
  { pattern: /text-cyan-100/g, replacement: 'text-white' },
  { pattern: /text-slate-950/g, replacement: 'text-white' },
  { pattern: /text-slate-200/g, replacement: 'text-slate-700' },
  { pattern: /text-red-300/g, replacement: 'text-rose-600' },
  { pattern: /text-emerald-200/g, replacement: 'text-emerald-700' },
  { pattern: /border-emerald-300(?:\/\d+)?/g, replacement: 'border-emerald-200' },
  { pattern: /bg-emerald-300(?:\/\d+)?/g, replacement: 'bg-emerald-50' },
  { pattern: /shadow-\[0_18px_40px_rgba\(2,6,23,0\.35\)\]/g, replacement: 'shadow-sm' },
  { pattern: /shadow-\[0_18px_40px_rgba\(2,6,23,0\.28\)\]/g, replacement: 'shadow-sm' }
];

function processDir(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      processDir(fullPath);
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
      let content = fs.readFileSync(fullPath, 'utf8');
      let modified = false;
      
      for (const { pattern, replacement } of replacements) {
        if (pattern.test(content)) {
          content = content.replace(pattern, replacement);
          modified = true;
        }
      }
      
      if (modified) {
        fs.writeFileSync(fullPath, content, 'utf8');
        console.log('Updated: ' + fullPath);
      }
    }
  }
}

for (const dir of dirs) {
  if (fs.existsSync(dir)) {
    processDir(dir);
  }
}
