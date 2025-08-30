from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import uvicorn

from .models import PrescriptionRequest, AnalysisResponse
from .routers import prescription

app = FastAPI(
    title="AI Medical Prescription Verification API",
    description="API for analyzing drug interactions, dosages, and alternatives",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prescription.router, prefix="/api/v1", tags=["prescription"])

@app.get("/")
async def root():
    return {"message": "AI Medical Prescription Verification API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "prescription-verification"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)