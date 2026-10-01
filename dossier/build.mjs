// Uso:  node dossier/build.mjs [es|ca|en|all]
// Genera dossier/out/Creative-Velas-Dossier-XX.pdf (A4 apaisado, 10 páginas).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { p, money } from './data.mjs';
import { slots } from './photos.config.mjs';
import { render } from './template.mjs';
import es from './i18n/es.mjs';
import ca from './i18n/ca.mjs';
import en from './i18n/en.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(here, 'out');
fs.mkdirSync(outDir, { recursive: true });

const langs = { es, ca, en };
const arg = process.argv[2] || 'all';
const todo = arg === 'all' ? Object.keys(langs) : [arg];

const fontsCss = fs.readFileSync(path.join(here, 'assets/fonts.css'), 'utf8').replaceAll("url('fonts/", "url('../assets/fonts/");
const css = fontsCss + '\n' + fs.readFileSync(path.join(here, 'template.css'), 'utf8');

const missing = new Set();
const photoUrl = (id) => {
  const file = path.join(here, 'assets/photos', `${id}.jpg`);
  if (fs.existsSync(file)) return `../assets/photos/${id}.jpg`;
  missing.add(id);
  return null;
};

const browser = await chromium.launch();
let problems = 0;
for (const lang of todo) {
  const f = money(lang);
  const c = langs[lang](p, f);
  const html = render({ c, p, f, lang, slots, photoUrl, css });
  const htmlPath = path.join(outDir, `dossier-${lang}.html`);
  fs.writeFileSync(htmlPath, html);

  const page = await browser.newPage();
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);

  // Control de desbordes: nada de contenido fuera del margen útil de cada página.
  const issues = await page.evaluate(() => {
    const mm = 96 / 25.4;
    const out = [];
    document.querySelectorAll('.page').forEach((pg, i) => {
      const r = pg.getBoundingClientRect();
      const isCover = pg.classList.contains('cover') || pg.classList.contains('contact-page');
      const maxBottom = r.top + 210 * mm - (isCover ? 0 : 12 * mm);
      const maxRight = r.left + 297 * mm - (isCover ? 0 : 12 * mm);
      pg.querySelectorAll('*').forEach((el) => {
        if (el.closest('.foot') || el.closest('.ph') || el.classList.contains('ph')) return;
        if (el.closest('.cover .right') || el.closest('.contact-page .photo')) return;
        const b = el.getBoundingClientRect();
        if (!b.width || !b.height) return;
        if (isCover && !pg.classList.contains('contact-page')) return;
        if (b.bottom > maxBottom + 1 || b.right > maxRight + 1) {
          out.push(`p${i + 1} <${el.tagName.toLowerCase()} class="${el.className}"> "${(el.textContent || '').trim().slice(0, 40)}" bottom=${Math.round((b.bottom - r.top) / mm)}mm right=${Math.round((b.right - r.left) / mm)}mm`);
        }
      });
    });
    return out;
  });
  if (issues.length) {
    problems += issues.length;
    console.log(`[${lang}] posibles desbordes:\n  ` + issues.slice(0, 12).join('\n  '));
  }

  const pdfPath = path.join(outDir, `Creative-Velas-Dossier-${lang.toUpperCase()}.pdf`);
  await page.pdf({ path: pdfPath, width: '297mm', height: '210mm', printBackground: true, preferCSSPageSize: true });
  await page.close();
  const kb = Math.round(fs.statSync(pdfPath).size / 1024);
  console.log(`[${lang}] ${path.relative(process.cwd(), pdfPath)} (${kb} KB)`);
}
await browser.close();
if (missing.size) console.log(`Fotos sin descargar (hueco neutro): ${[...missing].join(', ')}`);
console.log(problems ? `${problems} avisos de desborde` : 'Sin desbordes');
