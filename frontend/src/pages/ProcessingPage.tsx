import { C, HAND } from "../styles/tokens";

export function ProcessingPage() {
  return (
    <div style={{
      position: "absolute", inset: 0, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", gap: 34, padding: 32,
    }}>
      <div style={{
        position: "relative", width: 190, height: 250,
        background: C.white, borderRadius: 10,
        boxShadow: "0 10px 34px rgba(20,35,46,.14)",
        overflow: "hidden", border: `1px solid #e4eaee`,
      }}>
        <div style={{
          position: "absolute", left: 16, top: 16,
          fontFamily: HAND, fontSize: 26, color: C.red, fontWeight: 700,
        }}>Rx</div>
        <div style={{ position: "absolute", left: 16, top: 64, right: 16, display: "flex", flexDirection: "column", gap: 13 }}>
          {[80, 60, 72, 50, 66].map((w, i) => (
            <div key={i} style={{ height: 9, width: `${w}%`, background: "#e9eef1", borderRadius: 4 }} />
          ))}
        </div>
        <div style={{
          position: "absolute", left: 0, right: 0, height: 3,
          background: `linear-gradient(90deg,transparent,${C.brand},transparent)`,
          boxShadow: `0 0 14px 3px ${C.brand}66`,
          animation: "gsr-scan 1.8s ease-in-out infinite",
        }} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 13, minWidth: 300 }}>
        {[
          { es: "Extrayendo campos", en: "Extracting fields", delay: ".1s", active: true },
          { es: "Verificando en catálogo CIMA", en: "Verifying against CIMA catalog", delay: ".7s", active: false },
          { es: "Marcando abstenciones", en: "Flagging abstentions", delay: "1.3s", active: false },
        ].map(({ es, en, delay, active }) => (
          <div key={es} style={{
            display: "flex", alignItems: "center", gap: 11,
            color: active ? C.ink : C.dim,
            animation: `gsr-up .4s both`, animationDelay: delay,
          }}>
            {active ? (
              <span style={{
                width: 22, height: 22, borderRadius: "50%", flex: "0 0 auto",
                border: `2.5px solid ${C.brand}`, borderTopColor: "transparent",
                animation: "gsr-spin .8s linear infinite",
              }} />
            ) : (
              <span style={{
                width: 22, height: 22, borderRadius: "50%", flex: "0 0 auto",
                border: `2px solid #cdd8de`,
              }} />
            )}
            <span style={{ fontSize: 14.5, fontWeight: active ? 600 : 500 }}>
              {es} · {en}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
