// Plantilla HTML del dossier. Recibe el contenido ya traducido (i18n/*.mjs),
// las cifras (data.mjs) y el reparto de fotos (photos.config.mjs).

export function render({ c, p, f, lang, slots, photoUrl, css, standalone = false }) {
  const pct = (n) => (lang === 'en' ? `−${n}%` : `−${n} %`);
  const FALLBACK = 'linear-gradient(135deg,#eadfce,#dccbb4)';
  const phUrl = (url, pos, extra = '') =>
    `<div class="ph ${extra}" style="background-image:${url ? `url('${url.replace(/&/g, '&amp;')}'),` : ''}${FALLBACK};${pos ? `background-position:${pos};` : ''}"></div>`;
  const ph = (slot, extra = '') => {
    const s = slots[slot];
    return phUrl(s && photoUrl(s.id), s && s.pos, extra);
  };
  const tiles = (slot) => `<div class="tiles n${slots[slot].ids.length}">${slots[slot].ids.map((id) => phUrl(photoUrl(id))).join('')}</div>`;
  const foot = (n) => `<div class="foot"><span>${c.footer}</span><span>${String(n).padStart(2, '0')}</span></div>`;
  const li = (arr) => arr.map((t) => `<li>${t}</li>`).join('');
  const lb = (arr) => arr.map(([b, t]) => `<li><b>${b}</b> ${t}</li>`).join('');

  const tierHead = (t) =>
    `<th><span class="t">${t.to ? `${t.from}–${t.to} ${c.tariff.units}` : `${t.from} ${c.tariff.units} ${c.tariff.orMore}`}</span><span class="d">${pct(t.off)}</span></th>`;

  const pages = [];

  // 1 · Portada
  pages.push(`
<section class="page cover">
  <div class="left">
    <div class="wordmark">Creative Velas</div>
    <h1>${c.cover.tagline}</h1>
    <div class="kicker">${c.cover.kicker}</div>
    <p class="quote">${c.cover.quote}</p>
    <div class="contact">${p.contact.email} · ${c.phone} · ${p.contact.web}</div>
  </div>
  <div class="right">${ph('cover')}</div>
</section>`);

  // 2 · La marca
  pages.push(`
<section class="page">
  <div class="brand">
    <div>
      <div class="label">${c.brand.label}</div>
      <h2>${c.brand.title}</h2>
      <p class="lead" style="margin-top:5mm">${c.brand.p1}</p>
      <p class="lead">${c.brand.p2}</p>
      <div class="values">${c.brand.values.map(([b, t]) => `<div><b>${b}</b><span>${t}</span></div>`).join('')}</div>
      <div class="work"><div class="tag">${c.brand.workLabel}</div><ul class="dots">${li(c.brand.work)}</ul></div>
    </div>
    <figure class="pic">${ph('brand')}<figcaption>${c.brand.caption}</figcaption></figure>
  </div>
  ${foot(2)}
</section>`);

  // 3 · Dos formas de trabajar
  const way = (w, cls) => `<div class="card ${cls}"><div class="tag">${w.tag}</div><h3>${w.title}</h3><p>${w.text}</p><ul class="dots">${li(w.bullets)}</ul></div>`;
  pages.push(`
<section class="page ways">
  <div class="head">
    <div class="label">${c.ways.label}</div>
    <h2>${c.ways.title}</h2>
    <p class="lead">${c.ways.intro}</p>
  </div>
  <div class="two">${way(c.ways.a, 'a')}${way(c.ways.b, 'b')}</div>
  <div class="trio">
    <figure>${ph('waysA')}<figcaption>${c.ways.captions[0]}</figcaption></figure>
    <figure>${ph('waysB')}<figcaption>${c.ways.captions[1]}</figcaption></figure>
    <figure>${ph('waysC')}<figcaption>${c.ways.captions[2]}</figcaption></figure>
  </div>
  ${foot(3)}
</section>`);

  // 4 · Packs de alquiler
  const packCards = c.packs.items
    .map(
      (it, i) => `
    <div class="card pack ${p.packFrom[i] === p.minRental ? 'min' : ''}">
      ${ph('pack' + (i + 1))}
      <div class="body"><h3>${it.name}</h3><ul class="dots">${li(it.bullets)}</ul></div>
      <div class="price"><small>${c.packs.from}</small><b>${f(p.packFrom[i])}</b></div>
    </div>`
    )
    .join('');
  pages.push(`
<section class="page packs">
  <div class="head">
    <div class="label">${c.packs.label}</div>
    <h2>${c.packs.title}</h2>
    <p class="lead">${c.packs.intro}</p>
  </div>
  <div class="three">${packCards}</div>
  <div class="addons">
    <div class="tag">${c.packs.addonsLabel}</div>
    ${c.packs.addons.map(([b, s]) => `<div><b>${b}</b><span>${s}</span></div>`).join('')}
  </div>
  <p class="vat">${c.packs.vat}</p>
  ${foot(4)}
</section>`);

  // 5 · Condiciones
  pages.push(`
<section class="page terms">
  <div class="top">
    <div>
      <div class="label">${c.terms.label}</div>
      <h2>${c.terms.title}</h2>
      <ul class="items">${lb(c.terms.items)}</ul>
    </div>
    <div class="pics">
      <figure>${ph('termsA')}<figcaption>${c.terms.captions[0]}</figcaption></figure>
      <figure>${ph('termsB')}<figcaption>${c.terms.captions[1]}</figcaption></figure>
    </div>
  </div>
  <div class="cards">${c.terms.cards.map(([h, t]) => `<div class="card"><h3>${h}</h3><p>${t}</p></div>`).join('')}</div>
  ${foot(5)}
</section>`);

  // 6 · Colección
  const slotsColl = ['collLantern', 'collSunTr', 'collTr', 'collSoja'];
  pages.push(`
<section class="page coll">
  <div class="label">${c.collection.label}</div>
  <h2>${c.collection.title}</h2>
  <div class="items">${c.collection.items
    .map(
      (it, i) => `
    <div class="card item">
      ${ph(slotsColl[i])}
      <div class="body">
        <h3>${it.name}</h3><div class="sub">${it.sub}</div>
        <div class="detail">${it.detail}</div>
        <div class="price">${it.price}${it.priceNote ? `<small>${it.priceNote}</small>` : ''}</div>
      </div>
    </div>`
    )
    .join('')}</div>
  <div class="closed">
    <div class="tag">${c.collection.closedLabel}</div>
    ${c.collection.closed.map(([b, s]) => `<div><b>${b}</b><span>${s}</span></div>`).join('')}
  </div>
  <p class="note">${c.collection.note}</p>
  ${foot(6)}
</section>`);

  // 7 · Personalización y pedidos grandes
  pages.push(`
<section class="page custom">
  <div class="grid">
    <div>
      <div class="label">${c.custom.label}</div>
      <h2>${c.custom.title}</h2>
      <div class="do"><div class="tag">${c.custom.doLabel}</div><ul>${lb(c.custom.doItems)}</ul></div>
      <div class="card ceremony"><h3>${c.custom.ceremonyTitle}</h3><p>${c.custom.ceremonyText}</p></div>
      <div class="big">
        <div class="num">${c.custom.bigNumber}<small>${c.custom.bigUnit}</small></div>
        <div><h3>${c.custom.bigTitle}</h3><p>${c.custom.bigText}</p></div>
      </div>
    </div>
    <figure class="right">${ph('custom')}<figcaption>${c.custom.caption}</figcaption></figure>
  </div>
  ${foot(7)}
</section>`);

  // 8 · Tarifa profesional
  pages.push(`
<section class="page tariff">
  <div class="grid">
    <div>
      <div class="label">${c.tariff.label}</div>
      <h2>${c.tariff.title}</h2>
      <p class="sub">${c.tariff.sub}</p>
      <table>
        <thead><tr><th>${c.tariff.piece}</th>${p.tiers.map(tierHead).join('')}</tr></thead>
        <tbody>${c.tariff.rows.map(([k, name]) => `<tr><td>${name}</td>${p.tariff[k].map((n) => `<td>${f(n, true)}</td>`).join('')}</tr>`).join('')}</tbody>
      </table>
    </div>
    <div class="notes" style="margin-top:20mm">
      ${c.tariff.notes.map(([h, t]) => `<div class="card"><div class="tag">${h}</div><p>${t}</p></div>`).join('')}
    </div>
  </div>
  <div class="band">${tiles('tariffBand')}</div>
  ${foot(8)}
</section>`);

  // 9 · Proceso
  pages.push(`
<section class="page process">
  <div class="label">${c.process.label}</div>
  <h2>${c.process.title}</h2>
  <div class="steps">${c.process.steps
    .map(([h, t], i) => `<div class="step"><span class="n">${String(i + 1).padStart(2, '0')}</span><h3>${h}</h3><p>${t}</p></div>`)
    .join('')}</div>
  <div class="band">${tiles('processBand')}</div>
  ${foot(9)}
</section>`);

  // 10 · Contacto
  pages.push(`
<section class="page dark contact-page">
  <div class="left">
    <div class="label">${c.contact.label}</div>
    <h2>${c.contact.title}</h2>
    <p class="lead">${c.contact.text}</p>
    <div class="info">${c.contact.items.map(([k, v]) => `<div><small>${k}</small><span>${v}</span></div>`).join('')}</div>
    <div class="closing">${c.contact.closing}</div>
  </div>
  <div class="photo">${ph('contact', '')}</div>
  ${foot(10)}
</section>`);

  return `<!doctype html>
<html lang="${lang}"><head><meta charset="utf-8"><title>${c.docTitle}</title>
<style>${css}</style></head><body>${standalone ? `<div class="noprint bar"><span>${c.print.steps}</span><button onclick="window.print()">${c.print.button}</button></div>` : ''}${pages.join('\n')}</body></html>`;
}
