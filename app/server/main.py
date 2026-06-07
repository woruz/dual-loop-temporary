from fastapi import FastAPI
from app.server.routers import identity, webhook, dashboard

app = FastAPI(title="Dual-Loop Hexagonal Backend")

app.include_router(identity.router)
app.include_router(webhook.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Dual-Loop Hexagonal Backend!"}
