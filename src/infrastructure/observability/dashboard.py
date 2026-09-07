from prometheus_client import REGISTRY, CollectorRegistry


def _counter_total(
    registry: CollectorRegistry, name: str, label: str | None = None, value: str | None = None
) -> float:
    # Counter metric family names have their trailing "_total" stripped by
    # prometheus_client, but the samples keep the full name — match on the
    # sample name directly rather than the family name.
    total = 0.0
    for metric in registry.collect():
        for sample in metric.samples:
            if sample.name != name:
                continue
            if label is not None and sample.labels.get(label) != value:
                continue
            total += sample.value
    return total


def _histogram_avg_seconds(registry: CollectorRegistry, name: str) -> float | None:
    total_sum = 0.0
    total_count = 0.0
    for metric in registry.collect():
        if metric.name != name:
            continue
        for sample in metric.samples:
            if sample.name == f"{name}_sum":
                total_sum += sample.value
            elif sample.name == f"{name}_count":
                total_count += sample.value
    return (total_sum / total_count) if total_count > 0 else None


def render_dashboard_html(registry: CollectorRegistry = REGISTRY) -> str:
    """Renders a self-contained HTML dashboard from in-process Prometheus counters.

    All figures are cumulative since the API process started (no time series,
    no percentiles — that requires a real Prometheus server, which this
    project deliberately doesn't run; see adr-sin-despliegue-demo).
    """
    verified = _counter_total(registry, "gscan_verdicts_total", "status", "verified")
    uncertain = _counter_total(registry, "gscan_verdicts_total", "status", "uncertain")
    not_found = _counter_total(registry, "gscan_verdicts_total", "status", "not_found")
    total_verdicts = verified + uncertain + not_found
    hallucination_rate = (not_found / total_verdicts * 100) if total_verdicts else 0.0

    process_attempts = _counter_total(registry, "gscan_requests_total", "endpoint", "/process")
    abstentions = _counter_total(registry, "gscan_abstentions_total")
    abstention_rate = (abstentions / process_attempts * 100) if process_attempts else 0.0

    cost_usd = _counter_total(registry, "gscan_cost_usd_total")
    tokens = _counter_total(registry, "gscan_tokens_total")

    avg_latency_seconds = _histogram_avg_seconds(registry, "gscan_request_duration_seconds")
    latency_display = (
        f"{avg_latency_seconds * 1000:.1f} ms" if avg_latency_seconds is not None else "sin datos"
    )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>G-Scan-RX — Métricas</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0b0e14; color: #e6e6e6; padding: 2rem; }}
  h1 {{ font-size: 1.3rem; margin-bottom: 0.25rem; }}
  .note {{ color: #9aa0a6; font-size: 0.85rem; margin-bottom: 1rem; max-width: 65ch; }}
  .refresh-toggle {{
    font: inherit; font-size: 0.8rem; color: #e6e6e6; cursor: pointer;
    background: #161b22; border: 1px solid #2a2f3a; border-radius: 6px;
    padding: 0.4rem 0.7rem; margin-bottom: 1.5rem;
  }}
  .refresh-toggle:focus-visible {{ outline: 2px solid #5b9dd9; outline-offset: 2px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
  .card {{ background: #161b22; border: 1px solid #2a2f3a; border-radius: 8px; padding: 1rem; }}
  .card h2 {{ font-size: 0.85rem; color: #9aa0a6; margin: 0 0 0.4rem; font-weight: 500; }}
  .card .value {{ font-size: 1.8rem; font-weight: 600; }}
  .card .sub {{ font-size: 0.8rem; color: #9aa0a6; }}
</style>
</head>
<body>
<h1>G-Scan-RX — Dashboard de métricas</h1>
<p class="note">Acumulado desde que arrancó este proceso (sin historial ni percentiles).</p>
<button
  type="button"
  id="refresh-toggle"
  class="refresh-toggle"
  aria-pressed="true"
>⏸ Pausar auto-actualización (15s) · Pause auto-refresh</button>
<div class="grid">
  <div class="card">
    <h2>Alucinación (fármaco no encontrado en catálogo)</h2>
    <div class="value">{hallucination_rate:.1f}%</div>
    <div class="sub">{not_found:.0f} de {total_verdicts:.0f} veredictos de fármaco</div>
  </div>
  <div class="card">
    <h2>Abstención</h2>
    <div class="value">{abstention_rate:.1f}%</div>
    <div class="sub">{abstentions:.0f} de {process_attempts:.0f} intentos de /process</div>
  </div>
  <div class="card">
    <h2>Costo estimado</h2>
    <div class="value">${cost_usd:.2f}</div>
    <div class="sub">{tokens:.0f} tokens totales</div>
  </div>
  <div class="card">
    <h2>Latencia promedio</h2>
    <div class="value">{latency_display}</div>
    <div class="sub">todos los endpoints, promedio (no percentiles)</div>
  </div>
</div>
<script>
(function () {{
  var enabled = true;
  var timer = null;
  var btn = document.getElementById("refresh-toggle");

  function refresh() {{
    fetch(location.href)
      .then(function (r) {{ return r.text(); }})
      .then(function (html) {{
        var next = new DOMParser().parseFromString(html, "text/html");
        var nextGrid = next.querySelector(".grid");
        var curGrid = document.querySelector(".grid");
        if (nextGrid && curGrid) curGrid.innerHTML = nextGrid.innerHTML;
      }})
      .catch(function () {{ /* silent — next tick retries */ }});
  }}

  function schedule() {{
    if (timer) clearInterval(timer);
    timer = enabled ? setInterval(refresh, 15000) : null;
  }}

  btn.addEventListener("click", function () {{
    enabled = !enabled;
    btn.setAttribute("aria-pressed", String(enabled));
    btn.textContent = enabled
      ? "\\u23f8 Pausar auto-actualizaci\\u00f3n (15s) \\u00b7 Pause auto-refresh"
      : "\\u25b6 Reanudar auto-actualizaci\\u00f3n \\u00b7 Resume auto-refresh";
    schedule();
  }});

  schedule();
}})();
</script>
</body>
</html>
"""
