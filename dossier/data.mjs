// Cifras del dossier. Única fuente de verdad: los tres idiomas leen de aquí.
// Alquiler y tarifa profesional: sin IVA. Colección: PVP recomendado con IVA.

export const p = {
  // Packs de alquiler: precio "desde", sin IVA (Pack 2 marca el mínimo de alquiler)
  packFrom: [231, 182, 455],
  minRental: 182,
  extras: { lantern: 20.7, sun: 6.6 },

  // Alquiler: condiciones
  km: 30,
  perKm: 0.7,
  hours: 48,
  extraDayPct: 15,
  signalPct: 30,
  balanceDays: 7,
  depositPct: 20,
  depositMin: 100,
  quoteHours: 48,
  weeksAhead: '4-6',

  // Colección: PVP con IVA
  coll: { lantern: [30, 65, 120], sunTr: 22.5, tr: 25, soja: 3.5 },
  closed: { duo: 47.5, descubre: 29.5, coleccion: 54.5, multipack: 12.9 },

  // Tarifa profesional: precio por unidad, sin IVA. Columnas = tramos.
  minOrder: 10,
  tiers: [
    { from: 10, to: 24, off: 5 },
    { from: 25, to: 49, off: 10 },
    { from: 50, to: 99, off: 15 },
    { from: 100, to: null, off: 20 },
  ],
  tariff: {
    small: [23.55, 22.3, 21.1, 19.8],
    medium: [51.05, 48.35, 45.65, 43.0],
    large: [94.2, 89.25, 84.3, 79.35],
    sunTr: [17.65, 16.75, 15.8, 14.9],
    tr: [19.6, 18.6, 17.55, 16.5],
    soja: [2.75, 2.6, 2.45, 2.3],
  },

  contact: {
    email: 'creative.velas@gmail.com',
    phoneEs: '675 238 632',
    phoneIntl: '+34 675 238 632',
    web: 'creativevelas.com',
    ig: '@creative.velas',
    place: 'Lleger · Tarragona',
  },
};

// Formato de moneda por idioma: es/ca "22,50 €" · en "€22.50"
export function money(lang) {
  const fmt = (n, forceDec = false) => {
    const s = !forceDec && Number.isInteger(n) ? String(n) : n.toFixed(2);
    return lang === 'en' ? `€${s}` : `${s.replace('.', ',')} €`;
  };
  return fmt;
}
