"""
WCE Campus Assistant - FastAPI Backend
Main entry point for the API server.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from routes.chat import router as chat_router
from routes.upload import router as upload_router
from rag.pipeline import RAGPipeline

# Load environment variables
load_dotenv()

# Global RAG pipeline instance
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    Initializes the RAG pipeline on startup.
    """
    global rag_pipeline
    print("🚀 Starting WCE Campus Assistant Backend...")
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline()
    await rag_pipeline.initialize()
    
    # Store in app state for access in routes
    app.state.rag_pipeline = rag_pipeline
    
    print("✅ RAG Pipeline initialized successfully!")
    yield
    
    # Cleanup on shutdown
    print("🛑 Shutting down WCE Campus Assistant Backend...")


# Create FastAPI application
app = FastAPI(
    title="WCE Campus Assistant API",
    description="Backend API for the WCE Campus Assistant chatbot with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "WCE Campus Assistant API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "rag_pipeline": "initialized" if rag_pipeline else "not_initialized",
            "vector_db": "connected"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8001))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )
