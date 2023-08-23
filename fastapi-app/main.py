import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import redis
import uvicorn
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient

# FastAPI setup
app = FastAPI(
    title="MQTT Sensor Data API",
    description="A RESTful API for simulating sensor data, storing it in MongoDB, and providing data retrieval endpoints.",
    version="1.0.0",
)

# Configuring file handler for logging
log_file = f"{__file__}.log"
# Logging setup
logging.basicConfig(
    filename=log_file,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["sensor_data"]
collection = db["sensor_readings"]

# Redis setup
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"))
REDIS_PREFIX = "latest_readings:"
REDIS_LIMIT = 10  # Number of latest readings to store in Redis


class SensorReading(BaseModel):
    """
    Represents a sensor reading.

    Attributes:
        id (Optional[str]): The unique identifier of the reading.
        sensor_id (str): The unique identifier of the sensor.
        topic (float): The topic of the MQTT.
        value (float): The value reading.
        timestamp (datetime): The timestamp of the reading.
    """

    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()))
    sensor_id: str = Field(..., alias="sensorId")
    topic: str
    value: float
    timestamp: datetime

    @classmethod
    def from_bson(cls, data, *args, **kwargs) -> "SensorReading":
        """
        Create a SensorReading instance from BSON data.

        Args:
            data: BSON data.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            SensorReading: The created SensorReading instance.
        """
        try:
            data["id"] = str(data.pop("_id"))
        except Exception:
            logger.error("Error in data!")
        return cls(*args, **data, **kwargs)

    def as_response(self) -> Dict:
        """
        Convert the object to a dictionary for response.

        Returns:
            Dict: The dictionary representation of the object.
        """
        data = self.model_dump(by_alias=True)
        for field_name, value in self.model_fields.items():
            data_field = data.get(value.alias)
            if data_field:
                if type(value) is datetime:
                    # Converting the datetime into ISO8601 format
                    data[value.alias] = data[value.alias].isoformat()
        return data


@app.get("/")
async def read_root():
    """
    Root endpoint to welcome users.

    Returns:
        dict: Welcome message.
    """
    return {"message": "Welcome to the Sensor Data API"}


@app.get("/readings/", response_model=List[SensorReading])
async def get_sensor_readings(start: datetime, end: datetime = datetime.utcnow()):
    """
    Get sensor readings within a specified time range.

    Args:
        start (str): Start time.
        end (str): End time.

    Returns:
        List[SensorReading]: List of sensor readings.
    """
    try:
        readings = collection.find({"timestamp": {"$gte": start, "$lte": end}})
        # Convert and validate readings using the SensorReading model
        logger.info("Successfully fetched the data and sending the response!")
        return [SensorReading.from_bson(obj).as_response() for obj in readings]
    except Exception as e:
        logger.error(f"An error occurred while fetching sensor readings: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/last_ten_readings/", response_model=List[SensorReading])
async def get_last_ten_readings(sensor: str = "temperature"):
    """
    Get the last ten sensor readings for a specific sensor.

    Args:
        sensor (str): Sensor name, expects either temperature or humidity, default is temperature.

    Returns:
        List[SensorReading]: List of the last ten sensor readings.
    """
    try:
        redis_key = f"{REDIS_PREFIX}{sensor}"
        cached_readings = redis_client.lrange(redis_key, 0, REDIS_LIMIT - 1)

        if not cached_readings:
            logger.info("Cache miss. Fetching data from the database.")
            try:
                readings = (
                    collection.find({"topic": sensor})
                    .sort("timestamp", -1)
                    .limit(REDIS_LIMIT)
                )

                cached_readings = [
                    SensorReading.from_bson(obj).as_response() for obj in readings
                ]
                for reading in cached_readings:
                    reading["timestamp"] = str(reading["timestamp"])
                    redis_client.lpush(redis_key, json.dumps(reading))
                    redis_client.ltrim(redis_key, 0, REDIS_LIMIT - 1)
                logger.info(
                    "Successfully fetched the data from DB and updated in cache"
                )
            except Exception as e:
                logger.error("Error fetching data from the database: %s", e)
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail="Internal server error")
        else:
            logger.info("Found data in cache!, returning response")
            cached_readings = [json.loads(obj) for obj in cached_readings]
        return cached_readings
    except Exception as err:
        logger.error(f"Error while processing the request: {err}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
