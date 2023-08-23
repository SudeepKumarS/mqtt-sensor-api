import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, Optional

import redis
from bson import ObjectId
from paho.mqtt import client as mqtt_client
from pydantic import BaseModel, Field
from pymongo import MongoClient

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

# MQTT broker details
BROKER_ADDRESS = os.getenv("BROKER_HOST")
BROKER_PORT = 1883

# MongoDB details
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "sensor_data"
COLLECTION_NAME = "sensor_readings"

# MongoDB setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

redis_client = redis.Redis(host=os.getenv("REDIS_HOST"))
REDIS_KEY = "latest_readings:"
REDIS_LIMIT = 10  # Number of latest readings to store in Redis


# Database model
class SensorReading(BaseModel):
    """
    Represents a sensor reading.

    Attributes:
        id (Optional[str]): The unique identifier of the reading.
        sensor_id (str): The unique identifier of the sensor.
        topic (float): The topic of the MQTT.
        value (float): The value reading.
        timestamp (str): The timestamp of the reading.
    """

    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()))
    sensor_id: str = Field(..., alias="sensorId")
    topic: str
    value: float
    timestamp: datetime

    def to_bson(self, *args, **kwargs) -> Dict:
        """
        Convert the object to a BSON dict to store in DB.

        Returns:
            Dict: The BSON dictionary representation of the object.
        """
        data = self.model_dump(by_alias=True)
        data["_id"] = ObjectId(data.pop("id"))
        return data


def on_message(client, userdata, message):
    """
    MQTT on_message callback function.

    Args:
        client: The MQTT client instance.
        userdata: User data.
        message: The received MQTT message.
    """
    # Decoding the MQTT message
    payload = message.payload.decode("utf-8")
    topic = message.topic
    try:
        data = json.loads(payload)
        sensor_data = SensorReading(sensorId=data.get("sensor_id"), **data)
        # Inserting data into MongoDB
        collection.insert_one(sensor_data.to_bson())
        logger.info("Inserted data into MongoDB: %s", data)
        # Storing latest reading in Redis based on topic
        redis_client.lpush(f"{REDIS_KEY}{topic}", json.dumps(data))
        redis_client.ltrim(f"{REDIS_KEY}{topic}", 0, REDIS_LIMIT - 1)
        logger.info("Updated the cache with latest data")
    except json.JSONDecodeError as e:
        logger.error("Error parsing JSON: %s", e)
        logger.error(traceback.format_exc())


def on_connect(client, userdata, flags, rc):
    """
    MQTT on_connect callback function.

    Args:
        client: The MQTT client instance.
        userdata: User data.
        flags: Flags.
        rc: Return code.
    """
    if rc == 0:
        logger.info("Connected to Mosquitto MQTT Broker!")
    else:
        logger.error("Failed to connect, return code: %s", rc)


def main():
    client = mqtt_client.Client("MQTT")
    client.on_connect = on_connect
    client.connect(BROKER_ADDRESS, port=BROKER_PORT)
    client.subscribe("sensors/temperature")
    client.subscribe("sensors/humidity")
    client.on_message = on_message
    client.loop_forever()


if __name__ == "__main__":
    main()
