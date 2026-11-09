// Uso:  node social/fanales/build.mjs
// Carrusel de Instagram (5 diapositivas, 1080×1350) con las fotos de los fanales.
// Salida: social/fanales/out/slide-1.png … slide-5.png
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(here, 'out');
fs.mkdirSync(out, { recursive: true });

const fontsDir = path.join(here, '../../dossier/assets');
const fontsCss = fs.readFileSync(path.join(fontsDir, 'fonts.css'), 'utf8').replaceAll("url('fonts/", `url('${pathToFileURL(path.join(fontsDir, 'fonts')).href}/`);
const img = (n) => pathToFileURL(path.join(here, 'photos', `${n}.jpg`)).href;

const css = `${fontsCss}
:root{--ink:#2a211b;--ivory:#f4eee4;--accent:#a5673a;--gold:#e0b98f;--line:#d8c9b6}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Jost',sans-serif;font-weight:300;font-feature-settings:'lnum' 1;background:#888}
.slide{position:relative;width:1080px;height:1350px;overflow:hidden;background:var(--ivory);color:var(--ink)}
.slide.dark{background:var(--ink);color:var(--ivory)}
.photo{position:absolute;left:0;width:1080px;height:715px;background-size:cover;background-position:center}
.top .photo{top:0} .bottom .photo{bottom:0}
.wordmark{position:absolute;left:72px;font-weight:500;font-size:22px;letter-spacing:.5em;text-transform:uppercase}
.label{font-weight:500;font-size:22px;letter-spacing:.34em;text-transform:uppercase;color:var(--accent);display:flex;align-items:center;gap:20px}
.label::before{content:'';width:64px;height:2px;background:var(--accent)}
.dark .label{color:var(--gold)} .dark .label::before{background:var(--gold)}
h1,h2{font-family:'Cormorant Garamond',serif;font-weight:500;line-height:1.02;letter-spacing:-.01em}
em{font-style:italic;font-weight:400;color:var(--accent)} .dark em{color:var(--gold)}
.text{position:absolute;left:72px;right:72px}
.sub{font-size:31px;line-height:1.45;color:rgba(42,33,27,.86)} .dark .sub{color:rgba(244,238,228,.86)}
.handle{position:absolute;right:72px;font-weight:500;font-size:21px;letter-spacing:.3em;text-transform:uppercase;color:var(--accent)} .dark .handle{color:var(--gold)}
ul{list-style:none;margin-top:34px} li{position:relative;padding:18px 0 18px 46px;border-top:2px solid var(--line);font-size:32px;line-height:1.3}
li:last-child{border-bottom:2px solid var(--line)} li::before{content:'';position:absolute;left:0;top:37px;width:22px;height:2px;background:var(--accent)}
.dark li{border-color:rgba(244,238,228,.25)} .dark li::before{background:var(--gold)}
.swipe{position:absolute;left:72px;bottom:64px;font-weight:500;font-size:22px;letter-spacing:.34em;text-transform:uppercase;color:var(--gold)}
`;

const slides = [
  // 1 · Portada
  `<section class="slide dark top">
    <div class="wordmark" style="top:56px;color:var(--ivory)">Creative Velas</div>
    <div class="photo" style="top:130px;background-image:url('${img(3)}')"></div>
    <div class="text" style="top:900px">
      <h1 style="font-size:104px">Luz hecha a mano<br><em>para tus mesas</em></h1>
      <p class="sub" style="margin-top:26px;font-size:30px">Fanales de cera artesanales para eventos y bodas</p>
    </div>
    <div class="swipe">Desliza →</div><div class="handle" style="bottom:64px">@creative.velas</div>
  </section>`,
  // 2 · Mesa
  `<section class="slide top">
    <div class="photo" style="background-image:url('${img(5)}')"></div>
    <div class="text" style="top:780px">
      <div class="label">Centros de mesa</div>
      <h2 style="font-size:78px;margin-top:26px">La luz es lo único que se recuerda <em>de todas las mesas</em></h2>
    </div>
    <div class="handle" style="bottom:64px">@creative.velas</div>
  </section>`,
  // 3 · Pieza única
  `<section class="slide bottom">
    <div class="text" style="top:96px">
      <div class="label">Pieza única</div>
      <h2 style="font-size:92px;margin-top:28px">Cada fanal tiene <em>su propia textura</em></h2>
      <p class="sub" style="margin-top:26px">Hechos a mano, uno a uno, con cera que deja pasar la luz.</p>
    </div>
    <div class="photo" style="background-image:url('${img(1)}')"></div>
  </section>`,
  // 4 · Alquiler
  `<section class="slide top">
    <div class="photo" style="background-image:url('${img(6)}')"></div>
    <div class="text" style="top:770px">
      <div class="label">Alquiler para eventos</div>
      <h2 style="font-size:76px;margin-top:24px">Entrega, montaje y recogida <em>incluidos</em></h2>
      <ul><li>Packs ampliables pieza a pieza</li><li>Cera de soja natural incluida</li><li>Propuesta personalizada en menos de 48 h</li></ul>
    </div>
  </section>`,
  // 5 · Cierre
  `<section class="slide dark top">
    <div class="photo" style="background-image:url('${img(4)}')"></div>
    <div class="text" style="top:790px">
      <div class="label">Hablemos</div>
      <h2 style="font-size:92px;margin-top:26px">¿Preparamos <em>vuestro evento?</em></h2>
      <p class="sub" style="margin-top:28px">Escríbenos por WhatsApp o desde la web y os preparamos una propuesta sin compromiso.</p>
      <p style="margin-top:30px;font-family:'Cormorant Garamond',serif;font-weight:500;font-size:46px;color:var(--gold)">675 238 632 · creativevelas.com</p>
    </div>
    <div class="handle" style="bottom:64px">@creative.velas</div>
  </section>`,
];

const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><style>${css}</style></head><body>${slides.join('')}</body></html>`;
const htmlPath = path.join(out, 'carousel.html');
fs.writeFileSync(htmlPath, html);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
const els = await page.$$('.slide');
for (let i = 0; i < els.length; i++) {
  const f = path.join(out, `slide-${i + 1}.png`);
  await els[i].screenshot({ path: f });
  console.log(path.relative(process.cwd(), f));
}
await browser.close();
