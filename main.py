""""
This is the main file for the project.
FastAPI Backend is implemented here.
Connects to PostgreSQL with PostGIS and pgRouting.

done!
"""

from dotenv import load_dotenv  
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import logging
import os

from database_Creation import connect_Database, test_database_connection
from load_data import main as load_gtfs_data
from a_gtfs import router as gtfs
from a_stops_fastapi import router as stops
from a_realtime import router as realtime
from a_routing_fastapi import router as routes
from a_analysis_fastapi import router as analysis


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
   
    # Startup
    logger.info("Starting FastAPI application...")
    try:
        test_database_connection()
        logger.info("Database connection successful")
        logger.info("Loading GTFS data...")
        load_gtfs_data()
        logger.info("GTFS data loaded successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")

     
# Create FastAPI app
app = FastAPI(
    title="GTFS Route Planning API",
    description="Backend of project using GTFS data, PostGIS, and pgRouting",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gtfs, prefix="/gtfs")
app.include_router(stops, prefix="/stops")
app.include_router(realtime, prefix="/realtime")
app.include_router(routes, prefix="/routing")
app.include_router(analysis, prefix="/analysis")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/map")
def map_page():
    return FileResponse("template/index.html")

@app.get("/")
def root():
    return FileResponse("template/index.html")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
    )
