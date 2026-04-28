# ==================================================================
# FORGE - MAIN APP
# ==================================================================

from fastapi import FastAPI

# Import Database models  
app = FastAPI(
    title="The Forge API",
    description="S.P.E.C.I.A.L. Edition — Life Management RPG Backend",
    version="0.1.0",
)

# Import API routes
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}
