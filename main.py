""""
This is the main file for the project.
FastAPI Backend is implemented here.
Connects to PostgreSQL with PostGIS and pgRouting.

done!
"""

from fastapi import FastAPI
from dotenv import load_dotenv  
from contextlib import asynccontextmanager

import logging
import os

from database_Creation import test_database_connection
from a_gtfs import router as gtfs
from a_stops_fastapi import router as stops
from a_realtime import router as realtime
from a_routing_fastapi import router as routes


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
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
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


# Include routers
app.include_router(gtfs, prefix="/gtfs")
app.include_router(stops, prefix="/stops")
app.include_router(realtime, prefix="/realtime")
app.include_router(routes, prefix="/routing")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST")
    port = int(os.getenv("API_PORT"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
    )
