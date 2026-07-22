---
name: add-tool
description: Bootstrap de una nueva herramienta MCP para el cinturón del agente (contrato tipado + registro + fixture + tests) y su nota en la wiki. Úsalo cuando el usuario pida darle al agente una capacidad nueva. NO modifica tools existentes.
---

Workflow guiado para añadir una **herramienta MCP** al agente.

**Argumento:** `<name>` — slug lowercase de la tool (ej. `detect_anomaly`, `lookup_interaction`).

**Pasos (en orden):**

1. **Leer contexto obligatorio:**
   - `wiki/concepts/mcp.md` y `nucleo-agentico-react.md` (la LLM Wiki).
   - Una tool existente en `src/infrastructure/mcp/` (contrato, tipos, manejo de fallo).
   - Los `ports` del domain que la tool usará (nunca clases concretas).

2. **Definir el contrato tipado** (input/output Pydantic). La salida debe ser **verificable** y
   respetar el contrato de fallo: degradar (p.ej. `dudoso`/vacío), **nunca levantar** hacia el agente.

3. **Crear `src/infrastructure/mcp/$NAME.py`**: la tool usando ports; `tenacity` si hace I/O externo;
   sin `if __name__ == "__main__"`.

4. **Registrar** la tool en el servidor MCP (`fastmcp`) del proyecto.

5. **Crear `tests/fixtures/${NAME}_*.json`** (normal, faltante, edge) y
   `tests/infrastructure/mcp/test_$NAME.py` (mock de los bordes, sin red).

6. **Validar** con `/check`.

7. **Actualizar la LLM Wiki**: agregar la tool a la tabla de `wiki/concepts/mcp.md`; enlazar.

Reglas:
- Tarea **aditiva**: no toques tools ni tests existentes.
- Si la tool influye en lecturas/decisiones, respetá `abstencion-obligatoria` y
  `validacion-catalogo-obligatoria`.
