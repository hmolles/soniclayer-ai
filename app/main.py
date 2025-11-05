from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import evaluate, segments, audio, re_evaluate, summary

app = FastAPI(title="SonicLayer AI Backend")

# CORS setup for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(evaluate.router)
app.include_router(segments.router)
app.include_router(audio.router)
app.include_router(re_evaluate.router)
app.include_router(summary.router)