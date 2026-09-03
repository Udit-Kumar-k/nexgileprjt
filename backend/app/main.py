from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    organization,
    carbon,
    pcf,
    supplier,
    analytics,
    dashboard,
    compliance,
    integration
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Nexgile DecarbX — Enterprise Environmental Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware with explicit origins for browser credentialed requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
api_v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1)
app.include_router(organization.router, prefix=api_v1)
app.include_router(carbon.router, prefix=api_v1)
app.include_router(pcf.router, prefix=api_v1)
app.include_router(supplier.router, prefix=api_v1)
app.include_router(analytics.router, prefix=api_v1)
app.include_router(dashboard.router, prefix=api_v1)
app.include_router(compliance.router, prefix=api_v1)
app.include_router(integration.router, prefix=api_v1)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "database": "Supabase PostgreSQL / SQLite fallback"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
