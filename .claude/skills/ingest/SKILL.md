---
name: ingest
description: Incorpora lógica nueva (regla, concepto, entidad, value object, fuente, decisión) a la LLM Wiki del proyecto (vault de Obsidian) como nota Markdown linkeada. Úsala cuando el usuario proponga una regla/lógica nueva, diga "ingesta esto", "anotá esta decisión", o describa lógica que todavía no hay que programar. Las reglas nacen draft y NO se implementan hasta que Daniel las promueva a approved.
---

# Ingest — asentar lógica en la LLM Wiki

Convierte la idea/regla que pide el usuario en una nota Markdown linkeada dentro del vault.
**No programa nada**: deja una propuesta revisable.

**Ubicación del vault:** `~/projects/Vault Projects/G-Scan-RX/` (ajustar según la máquina). Leer su
`CLAUDE.md` para las convenciones completas.

## Pasos (en orden)

1. **Clasificar la nota** y elegir subcarpeta + plantilla (`templates/`):
   - Regla de negocio/seguridad → `wiki/rules/` con `templates/rule.md`.
   - Concepto transversal → `wiki/concepts/` con `templates/concept.md`.
   - Entidad de dominio → `wiki/entities/` con `templates/entity.md`.
   - Value object → `wiki/value-objects/` (base `templates/entity.md`).
   - Fuente/catálogo → `wiki/sources/` con `templates/source.md`.
   - Decisión de arquitectura → `wiki/decisions/`.

2. **Guardar material crudo** en `raw/` si la idea viene de un artículo/paper/link. Si es decisión
   directa del usuario, saltear.

3. **Crear la nota** en `kebab-case.md` con la plantilla y frontmatter obligatorio.
   - **Si es regla → `status: draft` SIEMPRE.** Nunca `approved` automático (las 5 invariantes de
     seguridad ya aprobadas son la excepción existente, no se re-crean).
   - `implements_in: [TBD]` hasta que se programe.

4. **Enlazar en ambos sentidos**: agregarla a `index.md` (en su sección) y a las notas relacionadas.

5. **Registrar en `log/<YYYY-MM-DD>.md`**: fecha, operación `ingest`, nota creada.

6. **Correr la skill `lint`.**

## Reglas
- **NO implementar la lógica en código** durante el ingest.
- Ante duda, dejar `draft` y preguntar. En este dominio, ante duda de seguridad, la nota prefiere
  abstención/validación/confirmación humana.
- Al terminar, reportar: qué nota se creó, en qué estado, y recordar que se implementa al promover.
