import { C } from "../styles/tokens";

export function Header() {
  return (
    <header style={{
      flex: "0 0 auto", height: 66, display: "flex", alignItems: "center",
      gap: 18, padding: "0 26px", background: C.white, borderBottom: `1px solid ${C.border}`,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9, background: C.brand,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="4" width="18" height="16" rx="2.5" stroke="#fff" strokeWidth="1.8"/>
            <path d="M3 9h18" stroke="#fff" strokeWidth="1.8"/>
            <path d="M7 13h6M7 16h9" stroke="#7fd4dd" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
        </div>
        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.05 }}>
          <span style={{ fontWeight: 700, fontSize: 17, letterSpacing: ".2px" }}>G-Scan-RX</span>
          <span style={{ fontSize: 11, color: C.dim, fontWeight: 500 }}>Rx digitization & verification</span>
        </div>
      </div>
      <div style={{ flex: 1 }} />
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "7px 14px", borderRadius: 999, background: C.brandBg, border: `1px solid ${C.brandBd}`,
      }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6l7-3z" stroke={C.brand} strokeWidth="1.8" strokeLinejoin="round"/>
          <path d="M9 12l2 2 4-4" stroke={C.brand} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span style={{ fontSize: 12.5, fontWeight: 600, color: "#08505f" }}>
          El sistema nunca adivina · The system never guesses
        </span>
      </div>
    </header>
  );
}
