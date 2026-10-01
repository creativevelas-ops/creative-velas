#!/usr/bin/env bash
# Descarga las fotos de la tienda Shopify listadas en photos.manifest.json
# y las deja optimizadas (máx. 1800 px, JPEG calidad 82) en assets/photos/.
# Requiere acceso de red a cdn.shopify.com, curl, jq e ImageMagick (convert).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p assets/photos .cache/original
ok=0; fail=0
while IFS=$'\t' read -r id url; do
  raw=".cache/original/${id}.jpg"
  if [ ! -s "$raw" ]; then
    if ! curl -sS -f -L -m 60 -o "$raw" "$url"; then echo "FALLO $id"; rm -f "$raw"; fail=$((fail+1)); continue; fi
  fi
  convert "$raw" -auto-orient -resize '1800x1800>' -strip -interlace Plane -quality 82 "assets/photos/${id}.jpg"
  ok=$((ok+1))
done < <(jq -r '.photos[] | [.id, .url] | @tsv' photos.manifest.json)
echo "Fotos listas: $ok · fallidas: $fail"
