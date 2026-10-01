// Uso:  node dossier/build.mjs [es|ca|en|all] [--pdf]
//
// Salida principal: dossier/out/Creative-Velas-Dossier-XX.html  (autocontenido)
//   · Las fuentes van incrustadas en el propio archivo.
//   · Las fotos se cargan desde la tienda Shopify al abrirlo en el navegador.
//   · El botón «Guardar como PDF» imprime las 10 páginas A4 apaisadas.
//
// Con --pdf genera además dossier/out/Creative-Velas-Dossier-XX.pdf, usando las fotos
// de assets/photos/ (se descargan con fetch-photos.sh). Sin fotos locales, esos huecos
// quedan en tono neutro.
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
const args = process.argv.slice(2);
const wantPdf = args.includes('--pdf');
const sel = args.find((a) => !a.startsWith('--')) || 'all';
const todo = sel === 'all' ? Object.keys(langs) : [sel];

const templateCss = fs.readFileSync(path.join(here, 'template.css'), 'utf8');
const fontsRaw = fs.readFileSync(path.join(here, 'assets/fonts.css'), 'utf8');
// HTML autocontenido: fuentes en base64
const cssStandalone =
  fontsRaw.replace(/url\('fonts\/([^']+)'\)/g, (_, fn) => `url('data:font/woff2;base64,${fs.readFileSync(path.join(here, 'assets/fonts', fn)).toString('base64')}')`) +
  '\n' + templateCss;
// PDF local: fuentes por ruta
const cssLocal = fontsRaw.replaceAll("url('fonts/", "url('../assets/fonts/") + '\n' + templateCss;

const manifest = JSON.parse(fs.readFileSync(path.join(here, 'photos.manifest.json'), 'utf8')).photos;
const remote = Object.fromEntries(manifest.map((m) => [m.id, `${m.url}&width=1600`]));
const remoteUrl = (id) => remote[id] ?? null;

const missing = new Set();
const localUrl = (id) => {
  if (fs.existsSync(path.join(here, 'assets/photos', `${id}.jpg`))) return `../assets/photos/${id}.jpg`;
  missing.add(id);
  return null;
};

const checkOverflow = (page) =>
  page.evaluate(() => {
    const mm = 96 / 25.4;
    const out = [];
    document.querySelectorAll('.page').forEach((pg, i) => {
      const r = pg.getBoundingClientRect();
      const full = pg.classList.contains('cover') || pg.classList.contains('contact-page');
      const maxBottom = r.top + 210 * mm - (full ? 0 : 12 * mm);
      const maxRight = r.left + 297 * mm - (full ? 0 : 12 * mm);
      pg.querySelectorAll('*').forEach((el) => {
        if (el.closest('.foot') || el.closest('.ph') || el.closest('.cover .right') || el.closest('.contact-page .photo')) return;
        if (pg.classList.contains('cover')) return;
        const b = el.getBoundingClientRect();
        if (!b.width || !b.height) return;
        if (b.bottom > maxBottom + 1 || b.right > maxRight + 1) {
          out.push(`p${i + 1} <${el.tagName.toLowerCase()} class="${el.className}"> "${(el.textContent || '').trim().slice(0, 40)}" bottom=${Math.round((b.bottom - r.top) / mm)}mm right=${Math.round((b.right - r.left) / mm)}mm`);
        }
      });
    });
    return out;
  });

const browser = await chromium.launch();
let problems = 0;
for (const lang of todo) {
  const f = money(lang);
  const c = langs[lang](p, f);

  // 1) HTML autocontenido (entregable)
  const html = render({ c, p, f, lang, slots, photoUrl: remoteUrl, css: cssStandalone, standalone: true });
  const htmlPath = path.join(outDir, `Creative-Velas-Dossier-${lang.toUpperCase()}.html`);
  fs.writeFileSync(htmlPath, html);

  // Verificación en el navegador de pruebas: maquetación sin desbordes y 10 páginas al imprimir.
  // (Aquí las fotos remotas no cargan por la red del entorno; se ve el tono neutro de reserva.)
  const page = await browser.newPage();
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => document.fonts.ready);
  const issues = await checkOverflow(page);
  if (issues.length) {
    problems += issues.length;
    console.log(`[${lang}] posibles desbordes:\n  ` + issues.slice(0, 12).join('\n  '));
  }
  const checkPdf = path.join(outDir, `.check-${lang}.pdf`);
  await page.pdf({ path: checkPdf, width: '297mm', height: '210mm', printBackground: true, preferCSSPageSize: true });
  await page.close();
  const pages = (fs.readFileSync(checkPdf, 'latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
  fs.rmSync(checkPdf);
  console.log(`[${lang}] ${path.relative(process.cwd(), htmlPath)} (${Math.round(fs.statSync(htmlPath).size / 1024)} KB, ${pages} páginas al imprimir)`);
  if (pages !== 10) problems++;

  // 2) PDF con fotos locales (opcional)
  if (wantPdf) {
    const htmlLocal = render({ c, p, f, lang, slots, photoUrl: localUrl, css: cssLocal });
    const localPath = path.join(outDir, `dossier-${lang}.local.html`);
    fs.writeFileSync(localPath, htmlLocal);
    const pg = await browser.newPage();
    await pg.goto(pathToFileURL(localPath).href, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    const pdfPath = path.join(outDir, `Creative-Velas-Dossier-${lang.toUpperCase()}.pdf`);
    await pg.pdf({ path: pdfPath, width: '297mm', height: '210mm', printBackground: true, preferCSSPageSize: true });
    await pg.close();
    console.log(`[${lang}] ${path.relative(process.cwd(), pdfPath)} (${Math.round(fs.statSync(pdfPath).size / 1024)} KB)`);
  }
}
await browser.close();
if (missing.size) console.log(`Fotos locales sin descargar (hueco neutro en el PDF): ${[...missing].join(', ')}`);
console.log(problems ? `${problems} avisos` : 'Sin desbordes');
