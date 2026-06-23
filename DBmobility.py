import requests
from google.transit import gtfs_realtime_pb2
import psycopg2
import time
from datetime import datetime

FEED_URL = "https://your-actual-rt-feed-url/vehicle_positions"
