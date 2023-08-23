import json
import logging
import os
import random
import time
from datetime import datetime
from uuid import uuid4

import paho.mqtt.client as mqtt

# MQTT broker details
BROKER_ADDRESS = os.getenv("BROKER_HOST")
BROKER_PORT = 1883

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

# Creating unique sensor IDs for each sensor
temp_sensor_id = str(uuid4())
hum_sensor_id = str(uuid4())


# Simulated sensor data generation for temperature
def generate_temperature_data() -> dict:
    """
    Generate random temperature data.

    Returns:
        dict: Generated sensor data.
    """
    temperature = round(20 + (30 * random.random()), 2)
    timestamp = datetime.utcnow().isoformat()  # ISO8601 format

    data = {
        "sensor_id": temp_sensor_id,
        "topic": "temperature",
        "value": temperature,
        "timestamp": timestamp,
    }
    return data


def generate_humidity_data() -> dict:
    """
    Generate random humidity data.

    Returns:
        dict: Generated sensor data.
    """
    humidity = round(40 + (60 * random.random()), 2)
    timestamp = datetime.utcnow().isoformat()

    data = {
        "sensor_id": hum_sensor_id,
        "topic": "humidity",
        "value": humidity,
        "timestamp": timestamp,
    }
    return data


def on_publish(client, userdata, mid):
    """
    MQTT on_publish callback function.

    Args:
        client: The MQTT client instance.
        userdata: User data.
        mid: Message ID.
    """
    logger.info(f"Message Published: {mid}")


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
        logger.error(f"Failed to connect, return code: {rc}")


# Create MQTT client instance
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

# Connect to broker
client.connect(BROKER_ADDRESS, port=BROKER_PORT)

# Start the MQTT loop
client.loop_start()

try:
    while True:
        sensor_data_temp = generate_temperature_data()
        sensor_data_hum = generate_humidity_data()
        temperature_payload = json.dumps(sensor_data_temp)
        humidity_payload = json.dumps(sensor_data_hum)

        # Publishing the topics
        client.publish("sensors/temperature", temperature_payload)
        client.publish("sensors/humidity", humidity_payload)

        time.sleep(15)  # Publish every 5 seconds
except KeyboardInterrupt:
    logger.info("Publisher stopped.")
    client.loop_stop()
    client.disconnect()
