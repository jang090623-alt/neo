const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + path.join(__dirname, 'manual.html'), { waitUntil: 'networkidle' });
  await p.pdf({ path: path.join(__dirname, 'manual.pdf'), width: '297mm', height: '210mm', printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
