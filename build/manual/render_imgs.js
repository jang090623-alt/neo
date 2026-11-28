// 단계 그림·확대 그림·아이콘을 PNG 로 저장. node render_imgs.js [단계번호들...]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const ROOT = path.join(__dirname, 'web'); const OUT = path.join(__dirname, 'img');
fs.mkdirSync(OUT, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.stl': 'application/octet-stream' };
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); });
(async () => {
  await new Promise(res => srv.listen(8765, res));
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('ERR', m.text()); });
  page.on('pageerror', e => console.log('PAGEERR', e.message));
  await page.goto('http://localhost:8765/render.html');
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  const steps = JSON.parse(fs.readFileSync(path.join(ROOT, 'steps.json')));
  const only = process.argv.slice(2).map(Number);
  const save = (f, url) => fs.writeFileSync(path.join(OUT, f), Buffer.from(url.split(',')[1], 'base64'));
  const icons = new Set();
  for (const st of steps) {
    st.call.forEach(c => icons.add(c[2]));
    if (only.length && !only.includes(st.n)) continue;
    const t = Date.now();
    save(`step${String(st.n).padStart(2, '0')}.png`, await page.evaluate(([s]) => window.renderStep(s, 1800, 1160, false), [st]));
    if (st.inset) save(`inset${String(st.n).padStart(2, '0')}.png`, await page.evaluate(([s]) => window.renderStep(s, 700, 700, true), [st]));
    console.log('step', st.n, Date.now() - t, 'ms');
  }
  if (!only.length || process.env.ICONS) for (const k of icons) save('icon_' + k.replace(/[:/]/g, '_') + '.png', await page.evaluate(([k]) => window.renderIcon(k, 300), [k]));
  // 표지·완성 그림
  if (!only.length || process.env.EXTRA) {
    const all = steps[steps.length - 1];
    const ped = steps.find(s => s.new.includes('ped_cable'));
    const hero = { ...all, new: [...all.ctx], ctx: [], explode: [0, 0, 0], view: { dir: [-1.0, 0.85, -0.75], up: [0, 1, 0] } };
    save('hero.png', await page.evaluate(([s]) => window.renderStep(s, 1800, 1160, false), [hero]));
    const heroB = { ...all, new: [...all.ctx], ctx: [], explode: [0, 0, 0], view: { dir: [0.9, 0.85, 1.0], up: [0, 1, 0] } };
    save('heroB.png', await page.evaluate(([s]) => window.renderStep(s, 1800, 1160, false), [heroB]));
    const pedal = { ...ped, new: [...ped.ctx, 'ped_cable'], ctx: [], explode: [0, 0, 0] };
    save('hero_pedal.png', await page.evaluate(([s]) => window.renderStep(s, 1000, 1000, false), [pedal]));
  }
  await browser.close(); srv.close();
})();
