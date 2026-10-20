import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import STORAGE_DIR
from app.database import init_db
from app.routes.lectures import router as lectures_router
from app.routes.personalization import router as personalization_router
from app.routes.failsafe import router as failsafe_router
from app.routes.tutor import router as tutor_router

# Initialize Database on startup
init_db()

app = FastAPI(
    title="ForOne AI-Personalized Education Platform API",
    description="Backend engine for hyper-personalized AI education with mission-critical fact failsafe verification.",
    version="1.0.0"
)

# Enable CORS for local Vite dev server and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(lectures_router)
app.include_router(personalization_router)
app.include_router(failsafe_router)
app.include_router(tutor_router)

# Mount local storage as static files for direct media streaming
if STORAGE_DIR.exists():
    app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

@app.get("/api/health")
def healthcheck():
    return {
        "status": "online",
        "service": "ForOne AI Platform",
        "version": "1.0.0",
        "free_tier_active": True,
        "failsafe_engine": "ACTIVE"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
