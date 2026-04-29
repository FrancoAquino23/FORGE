# ==================================================================
# FORGE - MAIN APP
# ==================================================================

from fastapi import FastAPI
from app.routers import auth, activities, player, forge, missions, prestige

# Import Database models  
app = FastAPI(
    title="The Forge API",
    description="S.P.E.C.I.A.L. Edition — Life Management RPG Backend",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(activities.router)
app.include_router(player.router)
app.include_router(forge.router)
app.include_router(missions.router)
app.include_router(prestige.router)

# Import API routes
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}
