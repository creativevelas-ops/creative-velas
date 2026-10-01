// Uso:  node dossier/summary.mjs
// Resumen de 2 páginas (A4 vertical) del dossier de alquiler y venta, listo para reenviar.
// Lee las cifras de data.mjs, así que siempre coincide con el dossier.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { p, money } from './data.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(here, 'out');
fs.mkdirSync(outDir, { recursive: true });

const f = money('es');
const pct = (n) => `−${n} %`;
const fontsCss = fs.readFileSync(path.join(here, 'assets/fonts.css'), 'utf8').replaceAll("url('fonts/", "url('../assets/fonts/");
const css = fontsCss + '\n' + fs.readFileSync(path.join(here, 'summary.css'), 'utf8');

const tierHead = (t) =>
  `<th><span class="t">${t.to ? `${t.from}–${t.to} uds` : `${t.from} uds o más`}</span><span class="d">${pct(t.off)}</span></th>`;
const tariffRows = [
  ['small', 'Fanal pequeño'], ['medium', 'Fanal mediano'], ['large', 'Fanal grande'],
  ['sunTr', 'Vela Sun Translucent'], ['tr', 'Vela Translucent'], ['soja', 'Vela Soja'],
];
const packs = [
  ['Pack 1 · Ceremonia & Bienvenida', '4 fanales XL artesanales · 6 Sun Lantern'],
  ['Pack 2 · Banquete & Centros de mesa', '10 Sun Lantern · 20 velas pequeñas de soja'],
  ['Pack 3 · Experiencia integral', '6 fanales XL · 12 Sun Lantern · 20 velas pequeñas de soja · set de la Ceremonia de la Luz de regalo'],
];
const qa = [
  ['¿Cuál es el mínimo para alquilar?', `${f(p.minRental)} sin IVA, el precio del Pack 2. Los packs se amplían pieza a pieza.`],
  ['¿Hay descuentos?', `En la compra profesional, del ${p.tiers[0].off} % al ${p.tiers[3].off} % según unidades (desde ${p.minOrder}). En el alquiler no hay tarifa de descuento: los pedidos grandes se valoran en el presupuesto.`],
  ['¿Qué incluye el alquiler?', 'Entrega, montaje, desmontaje, recogida y cera de soja natural. El cliente no almacena nada.'],
  ['¿Cuánto se paga al reservar?', `Una señal del ${p.signalPct} % del alquiler y la fianza (${p.depositPct} %, mínimo ${f(p.depositMin)}). El resto, ${p.balanceDays} días antes del evento.`],
  ['¿Y si se rompe algo?', 'Se descuenta de la fianza el coste de reposición. Si no hay incidencias, se devuelve íntegra tras revisar el material.'],
  ['¿Se puede personalizar?', 'Sí: frase en el fanal (hasta 40 caracteres) y color a elegir entre 11 tonos en fanales y 8 en velas translúcidas.'],
];
const steps = [
  ['Consulta gratuita', 'Fecha, espacio y número de mesas'],
  ['Presupuesto', `En menos de ${p.quoteHours} horas`],
  ['Reserva', 'Señal y fianza reembolsable'],
  ['Entrega y montaje', 'Coordinado con tu equipo'],
  ['Recogida', 'Nos encargamos de todo'],
];

const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Creative Velas · Resumen de alquiler y venta</title><style>${css}</style></head><body>

<section class="sheet">
  <div class="top"><span>Creative Velas</span><span>Resumen · Alquiler y venta</span></div>
  <h1>Alquiler y venta para eventos, <em>de un vistazo</em></h1>
  <p class="intro">Lo esencial para responder con seguridad a cualquier cliente. Los precios de alquiler y la tarifa profesional van sin IVA; los de la colección son PVP recomendado con IVA.</p>

  <div class="key">
    <div><b>${f(p.minRental)}</b><span>Mínimo de alquiler, sin IVA</span></div>
    <div><b>${p.quoteHours} h</b><span>Presupuesto personalizado, sin compromiso</span></div>
    <div><b>${p.minOrder} uds</b><span>Pedido mínimo en compra profesional</span></div>
    <div><b>${p.weeksAhead} sem</b><span>Reservar con antelación, sobre todo en primavera y otoño</span></div>
  </div>

  <div class="sec">
    <div class="label">Alquiler</div>
    <h2>Packs con montaje incluido</h2>
    <div class="sub">Llevamos, montamos, recogemos y nos encargamos de la cera. Precios desde, sin IVA.</div>
    <div class="packs">${packs
      .map(([n, t], i) => `<div class="pack ${p.packFrom[i] === p.minRental ? 'min' : ''}"><div><h3>${n}</h3><p>${t}</p></div><div class="price"><small>Desde</small><b>${f(p.packFrom[i])}</b></div></div>`)
      .join('')}</div>
    <p class="note"><b>Ampliaciones:</b> fanal extra ${f(p.extras.lantern, true)}/ud · Sun Lantern extra ${f(p.extras.sun, true)}/ud · velas pequeñas de soja, a consultar según número de mesas.</p>
  </div>

  <div class="sec">
    <div class="label">Alquiler</div>
    <h2>Condiciones</h2>
    <div class="cards">
      <div class="card"><small>Señal</small><b>${p.signalPct} %</b><span>al reservar; se descuenta del total. El resto, ${p.balanceDays} días antes del evento.</span></div>
      <div class="card"><small>Fianza</small><b>${p.depositPct} %</b><span>del alquiler, mínimo ${f(p.depositMin)}. Reembolsable tras revisar el material.</span></div>
      <div class="card"><small>Duración</small><b>${p.hours} horas</b><span>entre entrega y recogida. Día adicional: ${p.extraDayPct} % del alquiler.</span></div>
      <div class="card"><small>Desplazamiento</small><b>${p.km} km incluidos</b><span>después, ${f(p.perKm, true)} por kilómetro adicional sobre la distancia real.</span></div>
      <div class="card"><small>Si algo se rompe</small><b>Se descuenta</b><span>el coste de reposición de la fianza; sin incidencias, se devuelve íntegra.</span></div>
      <div class="card"><small>Incluido siempre</small><b>Todo</b><span>entrega, montaje, desmontaje, recogida y cera de soja natural.</span></div>
    </div>
  </div>

  <div class="sec" style="margin-top:6.5mm">
    <div class="label">El proceso, en cinco pasos</div>
    <div class="steps">${steps.map(([h, t], i) => `<div class="step"><span class="n">${String(i + 1).padStart(2, '0')}</span><b>${h}</b><span>${t}</span></div>`).join('')}</div>
  </div>

  <div class="foot"><span>creative.velas@gmail.com · ${p.contact.phoneEs} · ${p.contact.web}</span><span><b>1</b> / 2</span></div>
</section>

<section class="sheet">
  <div class="top"><span>Creative Velas</span><span>Resumen · Alquiler y venta</span></div>

  <div class="sec" style="margin-top:9mm">
    <div class="label">Compra de piezas</div>
    <h2>La colección</h2>
    <div class="sub">PVP recomendado, con IVA. Personalizable con una frase (hasta 40 caracteres); 11 colores en fanales y 8 en velas translúcidas.</div>
    <div class="cards four">
      <div class="card"><small>Fanal</small><b>Sun Lantern</b><span class="pr">${p.coll.lantern.join(' · ')} €</span><span>Pequeño · Mediano · Grande</span></div>
      <div class="card"><small>Vela</small><b>Sun Translucent</b><span class="pr">${f(p.coll.sunTr, true)}</span><span>Translúcida de diseño</span></div>
      <div class="card"><small>Vela</small><b>Translucent</b><span class="pr">${f(p.coll.tr)}</span><span>Translúcida, sin humo</span></div>
      <div class="card"><small>Vela</small><b>Soja</b><span class="pr">${f(p.coll.soja, true)}</span><span>Cera de soja 100 % natural</span></div>
    </div>
    <div class="strip">
      <div class="lbl">También en packs cerrados</div>
      <div><b>Dúo Translúcido</b><span>${f(p.closed.duo, true)}</span></div>
      <div><b>Pack Descubre · 3 velas</b><span>${f(p.closed.descubre, true)}</span></div>
      <div><b>Colección Completa · 4 velas</b><span>${f(p.closed.coleccion, true)}</span></div>
      <div><b>Multipack Soja · 4 velas</b><span>${f(p.closed.multipack, true)}</span></div>
    </div>
  </div>

  <div class="sec">
    <div class="label">Compra profesional</div>
    <h2>Tarifa por volumen</h2>
    <div class="sub">Precio por unidad, sin IVA. El precio de cada tramo se aplica a todas las unidades del pedido.</div>
    <table><thead><tr><th>Pieza</th>${p.tiers.map(tierHead).join('')}</tr></thead>
    <tbody>${tariffRows.map(([k, n]) => `<tr><td>${n}</td>${p.tariff[k].map((v) => `<td>${f(v, true)}</td>`).join('')}</tr>`).join('')}</tbody></table>
    <p class="note">Pedido mínimo profesional: <b>${p.minOrder} unidades</b>. De 1 a 9 unidades, precio de tienda. Más de 100 unidades, <b>presupuesto a medida</b> en menos de ${p.quoteHours} horas.</p>
  </div>

  <div class="sec">
    <div class="label">Preguntas frecuentes</div>
    <h2>Respuestas rápidas</h2>
    <div class="qa">${qa.map(([q, a]) => `<div><b>${q}</b><span>${a}</span></div>`).join('')}</div>
  </div>

  <div class="foot"><span>creative.velas@gmail.com · ${p.contact.phoneEs} · ${p.contact.web} · ${p.contact.ig}</span><span><b>2</b> / 2</span></div>
</section>
</body></html>`;

const htmlPath = path.join(outDir, 'Creative-Velas-Resumen.local.html');
fs.writeFileSync(htmlPath, html);
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);

// Control: ninguna página puede tener contenido que no quepa.
const issues = await page.evaluate(() => {
  const mm = 96 / 25.4;
  const out = [];
  document.querySelectorAll('.sheet').forEach((s, i) => {
    const r = s.getBoundingClientRect();
    const limit = r.top + 297 * mm - 18 * mm; // por encima del pie
    s.querySelectorAll('*').forEach((el) => {
      if (el.closest('.foot')) return;
      const b = el.getBoundingClientRect();
      if (b.width && b.height && b.bottom > limit) out.push(`p${i + 1} <${el.tagName.toLowerCase()}> "${(el.textContent || '').trim().slice(0, 30)}" bottom=${Math.round((b.bottom - r.top) / mm)}mm`);
    });
  });
  return out;
});
const pdfPath = path.join(outDir, 'Creative-Velas-Resumen-Alquiler-y-Venta.pdf');
await page.pdf({ path: pdfPath, width: '210mm', height: '297mm', printBackground: true, preferCSSPageSize: true });
await browser.close();
const pages = (fs.readFileSync(pdfPath, 'latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
console.log(`${path.relative(process.cwd(), pdfPath)} · ${pages} páginas · ${Math.round(fs.statSync(pdfPath).size / 1024)} KB`);
console.log(issues.length ? 'Posibles desbordes:\n  ' + issues.slice(0, 10).join('\n  ') : 'Sin desbordes');
