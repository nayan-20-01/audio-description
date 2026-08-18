from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="NPTEL Audio Description API")
app.include_router(router)
