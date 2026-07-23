from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.interfaces.api.dependencies import lifespan
from src.interfaces.api.middleware import PrometheusMiddleware
from src.interfaces.api.routers import agent, prescriptions

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="G-Scan-RX",
    version="0.3.0",
    description=(
        "Asistente de verificación de recetas médicas manuscritas. "
        "AVISO: este sistema NO reemplaza la validación farmacéutica profesional. "
        "Todo resultado requiere confirmación humana campo por campo."
    ),
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(PrometheusMiddleware)
app.include_router(prescriptions.router)
app.include_router(agent.router)
