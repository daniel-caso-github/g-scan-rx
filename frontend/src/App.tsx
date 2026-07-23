import { useRef, useState } from "react";
import { extractPrescription, verifyPrescription } from "./api/client";
import { fromApiMeds, SAMPLE } from "./hooks/useMedState";
import type { MedState } from "./hooks/useMedState";
import { Header } from "./components/Header";
import { UploadPage } from "./pages/UploadPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { ReviewPage } from "./pages/ReviewPage";
import { ConfirmedPage } from "./pages/ConfirmedPage";

type Screen = "upload" | "processing" | "review" | "done";

export default function App() {
  const [screen, setScreen] = useState<Screen>("upload");
  const [imageUrl, setImageUrl] = useState<string>("");
  const [meds, setMeds] = useState<MedState[]>([]);
  const [prescriptionId, setPrescriptionId] = useState<string>("");
  const [overallConf, setOverallConf] = useState<number>(0.74);
  const [result, setResult] = useState<"confirmed" | "rejected">("confirmed");
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  async function handleFile(file: File) {
    setImageUrl(URL.createObjectURL(file));
    setScreen("processing");
    setError(null);
    try {
      const extractRes = await extractPrescription(file);
      if (extractRes.error) { setError(extractRes.error.message); setScreen("upload"); return; }
      const rx = extractRes.data;
      setPrescriptionId(rx.id);

      const verifyRes = await verifyPrescription(rx);
      const verified = verifyRes.data;
      setOverallConf(verified?.overall_confidence ?? 0.74);
      setMeds(fromApiMeds(rx.medications, verified?.medications));
      setScreen("review");
    } catch {
      setError("Error de conexión con el servidor.");
      setScreen("upload");
    }
  }

  function handleSample() {
    setImageUrl("");
    setMeds(SAMPLE);
    setPrescriptionId("a3f9c2b1d4e8f7a0");
    setOverallConf(0.74);
    setScreen("processing");
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setScreen("review"), 2400);
  }

  function reset() {
    clearTimeout(timerRef.current);
    setScreen("upload");
    setMeds([]);
    setError(null);
  }

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Header />
      <main style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        {screen === "upload" && (
          <UploadPage onFile={handleFile} onSample={handleSample} error={error} />
        )}
        {screen === "processing" && <ProcessingPage />}
        {screen === "review" && (
          <ReviewPage
            imageUrl={imageUrl}
            initialMeds={meds}
            prescriptionId={prescriptionId}
            overallConfidence={overallConf}
            onConfirm={() => { setResult("confirmed"); setScreen("done"); }}
            onReject={() => { setResult("rejected"); setScreen("done"); }}
          />
        )}
        {screen === "done" && (
          <ConfirmedPage result={result} meds={meds} onReset={reset} />
        )}
      </main>
    </div>
  );
}
