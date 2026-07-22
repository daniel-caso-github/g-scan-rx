from fastapi import FastAPI

from src.interfaces.api.dependencies import lifespan
from src.interfaces.api.routers import agent, prescriptions

app = FastAPI(
    title="G-Scan-RX",
    version="0.2.0",
    description=(
        "Asistente de verificación de recetas médicas manuscritas. "
        "AVISO: este sistema NO reemplaza la validación farmacéutica profesional. "
        "Todo resultado requiere confirmación humana campo por campo."
    ),
    lifespan=lifespan,
)

app.include_router(prescriptions.router)
app.include_router(agent.router)
