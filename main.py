""""
This is the main file for the project.
FastAPI Backend is implemented here.
Connects to PostgreSQL with PostGIS and pgRouting.

done!
"""

from dotenv import load_dotenv  
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import logging
import os
import uvicorn


from database_Creation import test_database_connection
from load_data import main as load_gtfs_data


from Ra_explorer import router as explorer
from Ra_routing import router as routes
from Ra_Spail_tools import router as spail_tools
from Ra_advanced import router as advanced
from Ra_mobilityDB import router as mobilitydb

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
        #load_gtfs_data()
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


# Include routers
app.include_router(explorer, prefix="/explorer")
app.include_router(routes, prefix="/routes")
app.include_router(spail_tools, prefix="/spail-tools")
app.include_router(advanced, prefix="/advanced")
app.include_router(mobilitydb, prefix="/mobilitydb")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/map")
def map_page():
    return FileResponse("template/index.html")

@app.get("/")
def root():
    return FileResponse("template/index.html")

if __name__ == "__main__":    
    host = os.getenv("API_HOST")
    port = int(os.getenv("API_PORT"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
    )
