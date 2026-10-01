// Qué foto va en cada hueco del dossier. Los ids salen de photos.manifest.json.
// `pos` ajusta el encuadre (background-position) si hace falta.
// `ids` = franja con varias fotos en fila.
export const slots = {
  cover: { id: 'sl-01', pos: 'center 45%' },
  brand: { id: 'sl-02' },
  waysA: { id: 'sl-03' },
  waysB: { id: 'tr-02' },
  waysC: { id: 'pk-01' },
  pack1: { id: 'sl-04' },
  pack2: { id: 'sl-07' },
  pack3: { id: 'sl-08' },
  termsA: { id: 'sl-09' },
  termsB: { id: 'st-02' },
  collLantern: { id: 'sl-10' },
  collSunTr: { id: 'st-01' },
  collTr: { id: 'tr-01' },
  collSoja: { id: 'so-01' },
  custom: { id: 'sl-11' },
  tariffBand: { ids: ['pk-01', 'pk-02', 'pk-03', 'so-05'] },
  processBand: { ids: ['sl-14', 'sl-15', 'st-03'] },
  contact: { id: 'sl-12' },
};
