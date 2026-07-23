const BASE_URL = "";

export async function extractPrescription(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/extract`, { method: "POST", body: form });
  return res.json();
}

export async function verifyPrescription(prescription: unknown) {
  const res = await fetch(`${BASE_URL}/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prescription),
  });
  return res.json();
}

export async function startAgent(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/agent/start`, { method: "POST", body: form });
  return res.json();
}

export async function confirmAgent(threadId: string, confirmedFields: Record<string, unknown>) {
  const res = await fetch(`${BASE_URL}/agent/${threadId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed_fields: confirmedFields }),
  });
  return res.json();
}
