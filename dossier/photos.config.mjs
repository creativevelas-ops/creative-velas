// Qué foto va en cada hueco del dossier. Los ids salen de photos.manifest.json.
// `pos` ajusta el encuadre (background-position) si hace falta.
// Si una foto no está descargada, el hueco se pinta con un tono neutro y el build avisa.
export const slots = {
  cover: { id: 'sl-01', pos: 'center 40%' },
  brand: { id: 'sl-02', pos: 'center' },
  waysCeremony: { id: 'sl-03' },
  waysBanquet: { id: 'sl-04' },
  waysGift: { id: 'pk-01' },
  pack1: { id: 'sl-05' },
  pack2: { id: 'sl-06' },
  pack3: { id: 'sl-07' },
  termsA: { id: 'sl-08' },
  termsB: { id: 'sl-09' },
  collLantern: { id: 'sl-10' },
  collSunTr: { id: 'st-01' },
  collTr: { id: 'tr-01' },
  collSoja: { id: 'so-01' },
  custom: { id: 'sl-11' },
  tariffBand: { id: 'sl-12', pos: 'center 55%' },
  processBand: { id: 'sl-13', pos: 'center 50%' },
  contact: { id: 'sl-14', pos: 'center' },
};
