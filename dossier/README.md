# Dossier profesional · Creative Velas

Dossier de eventos y bodas (alquiler y venta) en tres idiomas: español, catalán e inglés.
A4 apaisado, 10 páginas. Se genera desde código, así que cualquier cambio de texto o de
precio se hace en un solo sitio y se vuelve a generar el PDF.

## Generar el dossier

```bash
node dossier/build.mjs        # los tres idiomas
node dossier/build.mjs es     # solo uno (es | ca | en)
node dossier/build.mjs --pdf  # además, PDF con las fotos descargadas en assets/photos/
```

La salida principal son tres archivos HTML autocontenidos en `dossier/out/`
(`Creative-Velas-Dossier-ES.html`, `-CA`, `-EN`):

- Las fuentes van incrustadas en el propio archivo.
- Las fotos se cargan desde la tienda Shopify al abrirlo en el navegador.
- El botón «Guardar como PDF» de la barra superior imprime las 10 páginas A4 apaisadas
  (en la ventana de impresión: tamaño A4 apaisado, márgenes «Ninguno», «Gráficos de fondo» activado).

El script avisa si algún texto se sale del margen de la página y comprueba que al imprimir salen 10 páginas.

Requisitos: Node 22 y el paquete `playwright` con Chromium.

## Qué tocar para cambiar algo

| Quiero cambiar… | Archivo |
|---|---|
| Un precio, un porcentaje, un plazo | `data.mjs` (se aplica a los tres idiomas) |
| Un texto | `i18n/es.mjs`, `i18n/ca.mjs`, `i18n/en.mjs` |
| Qué foto va en cada hueco | `photos.config.mjs` |
| Colores, tipografías, tamaños | `template.css` |
| El orden o la estructura de las páginas | `template.mjs` |

## Fotos

Las fotos salen de la tienda Shopify (creativevelas.com). La lista está en
`photos.manifest.json` y el reparto por huecos en `photos.config.mjs`. Para cambiar una foto,
se cambia el id del hueco en `photos.config.mjs`; los ids disponibles están en el manifiesto.

Para generar un PDF directamente desde el código (sin pasar por el navegador) hay que
descargar antes las fotos:

```bash
dossier/fetch-photos.sh
node dossier/build.mjs --pdf
```

Eso necesita acceso de red a `cdn.shopify.com`, además de `curl`, `jq` e ImageMagick.
Si una foto no está, el hueco se pinta con un tono neutro.

## Condiciones fijadas

- Alquiler: mínimo 182 € (Pack 2). Señal del 30 %, resto 7 días antes. Fianza del 20 % (mínimo 100 €).
  Hasta 48 h entre entrega y recogida; día adicional, 15 % del alquiler.
- Compra: de 1 a 9 uds precio de tienda; tarifa profesional desde 10 uds con tramos
  10-24 (−5 %), 25-49 (−10 %), 50-99 (−15 %) y 100 o más (−20 %). Más de 100: presupuesto a medida.
- Alquiler y tarifa profesional, sin IVA. Colección, PVP con IVA.
