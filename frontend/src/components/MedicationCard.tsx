import { C, MONO } from "../styles/tokens";
import type { MedState } from "../hooks/useMedState";
import { fieldBucket } from "../hooks/useMedState";

const FIELD_LABELS: Record<string, [string, string]> = {
  drug:      ["Medicamento", "Drug"],
  dose:      ["Dosis",       "Dose"],
  frequency: ["Frecuencia",  "Frequency"],
  duration:  ["Duración",    "Duration"],
  route:     ["Vía",         "Route"],
};

const VERDICTS = {
  verified:     { symbol: "✓", es: "Verificado",   en: "Verified",   c: [C.green, C.greenBg, C.greenBd] },
  uncertain:    { symbol: "⚠", es: "Revisar dosis", en: "Check dose", c: [C.amber, C.amberBg, C.amberBd] },
  no_encontrado:{ symbol: "✗", es: "No encontrado", en: "Not found",  c: [C.red,   C.redBg,   C.redBd  ] },
} as const;

const BUCKET_CHIP = {
  readable:  { icon: "●", es: "Legible",     en: "Readable",    color: C.green, bg: C.greenBg, bd: C.greenBd },
  uncertain: { icon: "▲", es: "Dudoso",      en: "Uncertain",   color: C.amber, bg: C.amberBg, bd: C.amberBd },
  abstention:{ icon: "⊘", es: "Abstención",  en: "Abstention",  color: C.red,   bg: C.redBg,   bd: C.redBd   },
  corrected: { icon: "✓", es: "Corregido",   en: "Corrected",   color: C.green, bg: C.greenBg, bd: C.greenBd },
  resolved:  { icon: "✓", es: "Completado",  en: "Filled in",   color: C.green, bg: C.greenBg, bd: C.greenBd },
};

interface Props {
  med: MedState;
  index: number;
  focused: string | null;
  onFocus: (id: string | null) => void;
  onFieldChange: (fieldKey: string, value: string) => void;
}

export function MedicationCard({ med, index, focused, onFocus, onFieldChange }: Props) {
  const v = VERDICTS[med.verdict.status];
  const [vc, vbg, vbd] = v.c;
  const matchPct = Math.round((med.verdict.match_score ?? 0) * 100);
  const drugField = med.fields.find(f => f.key === "drug");
  const drugUnread = drugField?.status === "unreadable" && !drugField.value.trim();
  const name = drugUnread ? "No legible" : (drugField?.value || med.drugRaw);
  const catalogLine = med.verdict.status === "no_encontrado"
    ? "Sin coincidencia en catálogo · No catalog match"
    : `CIMA ${med.verdict.catalog_id} · ${matchPct}% coincidencia · ${matchPct}% match`;

  return (
    <div style={{
      flex: "0 0 auto", background: C.white, border: `1px solid ${C.border}`,
      borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 3px rgba(20,35,46,.05)",
    }}>
      {/* card header */}
      <div style={{
        display: "flex", alignItems: "center", gap: 14,
        padding: "15px 18px", borderBottom: `1px solid #eef2f4`,
      }}>
        <span style={{
          width: 30, height: 30, borderRadius: 8, background: C.brandBg,
          color: C.brand, fontWeight: 700, fontSize: 14,
          display: "flex", alignItems: "center", justifyContent: "center",
          flex: "0 0 auto", fontFamily: MONO,
        }}>{index + 1}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 17, fontWeight: 700, color: drugUnread ? C.red : C.ink }}>
            {name}
          </div>
          <div style={{ fontSize: 12, color: C.dim, fontFamily: MONO, marginTop: 2 }}>
            {catalogLine}
          </div>
        </div>
        <div style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          padding: "6px 12px", borderRadius: 999,
          fontSize: 12.5, fontWeight: 600, color: vc, background: vbg,
          border: `1px solid ${vbd}`, whiteSpace: "nowrap", flex: "0 0 auto",
        }}>
          <span style={{ fontSize: 14, lineHeight: 1 }}>{v.symbol}</span>
          <span>{v.es} · {v.en}</span>
        </div>
      </div>

      {/* fields */}
      <div style={{ display: "flex", flexDirection: "column" }}>
        {med.fields.map(f => {
          const id = `${index}-${f.key}`;
          const isFocused = focused === id;
          const bucket = fieldBucket(f);
          const chip = BUCKET_CHIP[bucket];
          const editable = f.status === "uncertain" || f.status === "unreadable";
          const isAbst = bucket === "abstention";
          const [le, len] = FIELD_LABELS[f.key] ?? [f.key, f.key];

          return (
            <div
              key={f.key}
              onMouseEnter={() => onFocus(id)}
              onMouseLeave={() => onFocus(null)}
              style={{
                display: "flex", gap: 14, alignItems: "flex-start",
                padding: "13px 18px", borderTop: "1px solid #f1f4f6",
                transition: "background .12s",
                background: isFocused ? C.brandBg : isAbst ? "#fdf4f4" : "transparent",
              }}
            >
              <div style={{ flex: "0 0 118px", paddingTop: 2 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{le}</div>
                <div style={{ fontSize: 11.5, color: "#9aa7b0", marginTop: -1 }}>{len}</div>
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                {!editable ? (
                  <span style={{ fontSize: 15, fontWeight: 500, color: C.ink }}>{f.value}</span>
                ) : (
                  <input
                    value={f.value}
                    placeholder={isAbst ? "Complete el valor · Enter value" : "Corrija si procede · Correct if needed"}
                    onFocus={() => onFocus(id)}
                    onChange={e => onFieldChange(f.key, e.target.value)}
                    style={{
                      width: "100%", maxWidth: 220, padding: "8px 11px",
                      borderRadius: 8, fontSize: 14, color: C.ink, outline: "none",
                      background: C.white,
                      border: isAbst
                        ? `1.5px dashed ${C.red}; box-shadow: 0 0 0 3px ${C.redBg}`
                        : (bucket === "corrected" || bucket === "resolved")
                          ? `1.5px solid ${C.greenBd}`
                          : `1.5px solid ${C.amberBd}`,
                      boxShadow: isAbst ? `0 0 0 3px ${C.redBg}` : undefined,
                    }}
                  />
                )}
              </div>

              <div style={{
                flex: "0 0 auto", display: "flex", flexDirection: "column",
                alignItems: "flex-end", gap: 5, minWidth: 132,
              }}>
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 5,
                  padding: "3px 9px", borderRadius: 999, fontSize: 11, fontWeight: 600,
                  color: chip.color, background: chip.bg, border: `1px solid ${chip.bd}`,
                  whiteSpace: "nowrap",
                }}>
                  <span style={{ fontSize: 11, lineHeight: 1 }}>{chip.icon}</span>
                  {chip.es} · {chip.en}
                </span>
                {bucket !== "abstention" && (
                  <span style={{ fontSize: 11, color: "#9aa7b0", fontFamily: MONO }}>
                    conf {Math.round(f.confidence * 100)}%
                  </span>
                )}
                {isAbst && (
                  <span style={{ fontSize: 10.5, color: C.red, textAlign: "right", lineHeight: 1.3, maxWidth: 150 }}>
                    El sistema no adivinó · System did not guess
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
