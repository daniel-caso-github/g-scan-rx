import hashlib

from fastapi import FastAPI, File, UploadFile

from src.interfaces.api.dependencies import get_extract_prescription_use_case

app = FastAPI(title="G-Scan-RX", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    use_case = get_extract_prescription_use_case()
    prescription = await use_case.execute(image_bytes, image_hash)
    return prescription.model_dump()
