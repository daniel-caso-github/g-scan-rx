---
name: lint
description: Verifica la consistencia de la LLM Wiki del proyecto (vault de Obsidian) tras cambios — links rotos, notas huérfanas, duplicados, frontmatter y coherencia spec↔código. Úsala después de un ingest o cualquier edición del vault. Solo reporta; no auto-corrige salvo pedido explícito.
---

# Lint — control de calidad de la LLM Wiki

Corre después de cualquier `ingest`/edición del vault (`~/projects/Vault Projects/G-Scan-RX/`).

## Qué verificar
1. **Links rotos** — todo `[[wikilink]]` apunta a una nota existente (ignorar placeholders de
   `templates/` y de prosa: `[[wikilink]]`, `[[x]]`, `[[<...>]]`).
2. **Notas huérfanas** — toda nota de `wiki/` y `log/` está referenciada desde al menos otra.
3. **Duplicados** — no hay dos notas sobre lo mismo → proponer merge.
4. **Frontmatter** — toda nota de contenido empieza con `---` y tiene campos obligatorios + `status`
   válido (`draft`/`approved`/`deprecated` en reglas).
5. **Coherencia spec↔código** — si una regla `approved` cambió y su `implements_in` ya no coincide con
   el código, **señalarlo** (no editar código desde el lint).

## Script de apoyo
```bash
VAULT="$HOME/projects/Vault Projects/G-Scan-RX"; cd "$VAULT" || exit 1
existing=$(find . -name '*.md' -not -path './templates/*' -not -path './.obsidian/*' | sed 's|.*/||; s|\.md$||' | sort -u)
grep -rhoE '\[\[[^]]+\]\]' --include=*.md . --exclude-dir=templates --exclude-dir=.obsidian \
  | sed -E 's/\[\[([^]|#]+)([|#][^]]*)?\]\]/\1/' | sed 's|.*/||' | sort -u \
  | while read -r t; do [ -n "$t" ] && ! grep -qxF "$t" <<< "$existing" && echo "ROTO: [[$t]]"; done
for f in $(find wiki log -name '*.md'); do b=$(basename "$f" .md); \
  n=$(grep -rlE "\[\[$b(\||\]|#)" --include=*.md . --exclude-dir=templates --exclude-dir=.obsidian | grep -v "$f" | wc -l); \
  [ "$n" -eq 0 ] && echo "HUERFANA: $f"; done
for f in $(find wiki log -name '*.md'); do [ "$(head -1 "$f")" != "---" ] && echo "SIN FM: $f"; done
```

## Reglas
- **Solo reportar** por defecto. No borrar ni reescribir salvo pedido explícito.
- Los `[[wikilink]]`, `[[x]]`, `[[<...>]]` de `templates/` o de ejemplos en prosa son placeholders
  esperados — no son fallos.
- Output final compacto: `✓ links OK | ✓ sin huérfanas | ✓ frontmatter OK`, o la lista de problemas
  con una acción por cada uno.
