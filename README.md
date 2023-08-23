## Project Documentation

### Overview

This project simulates the behavior of sensors, monitors their readings, and provides APIs to retrieve data based on specific criteria. It uses Docker and Docker Compose to orchestrate various services, including a Mosquitto MQTT broker, MQTT publisher, MQTT subscriber, FastAPI application, MongoDB, and Redis.

### Project Structure

The project is organized into the following components:

- **mqtt-publisher:** Contains the MQTT publisher code that generates and publishes simulated sensor data.
- **mqtt-subscriber-mongodb:** Contains the MQTT subscriber code that receives and stores sensor data in MongoDB and Redis.
- **fastapi-api:** Contains the FastAPI application code that provides APIs for retrieving sensor data from MongoDB and Redis.
- **docker-compose.yml:** The Docker Compose file that defines the services and their configurations.

### Setup Instructions

1. Make sure you have Docker and Docker Compose installed on your system.

2. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/SudeepKumarS/mqtt-sensor-api.git
   cd mqtt-sensor-api
   ```

3. Navigate to the project directory:

   ```bash
   cd mqtt-sensor-api
   ```

4. Run the Docker Compose command to start all the services:

   ```bash
   docker-compose up
   ```

5. Once the services are up and running, you can access the FastAPI application at `http://localhost:8000`.

### Interacting with the System

#### MQTT Publisher

The MQTT publisher simulates sensor data and publishes it to MQTT topics. No further interaction is needed for this component.

#### MQTT Subscriber and MongoDB

The MQTT subscriber receives sensor data and stores it in MongoDB. No direct interaction is needed for this component.

#### FastAPI Application

You can access the FastAPI application's endpoints using a web browser or a tool like `curl`. Here are the available endpoints:

- `GET /`: Welcomes users to the Sensor Data API.
- `GET /readings/`: Retrieves sensor readings within a specified time range.
- `GET /latest_ten_readings/`: Retrives latest ten readings based on the sensor type.

To retrieve sensor readings, you can use tools like `curl` or a web browser:

```bash
# Example to retrieve readings using curl
curl "http://localhost:8000/readings/?start=<start_time>&end=<end_time>"
curl "http://localhost:8000/last_ten_readings/?sensor=<sensor_type>"
```

or

You can head to the [Swagger UI docs](http://localhost:8000/docs) to interact with the API endpoints and retrieve the data. 
Replace `<start_time>`, `<end_time>` and `<sensor_type>` with appropriate values.

### Clean Up

To stop the services and remove the containers, run:

```bash
docker-compose down
```

## Design Choices

### Use of Docker and Docker Compose

I chose to utilize Docker and Docker Compose to manage our project's various components and services. Docker containers provide a consistent and isolated environment for each service, ensuring that dependencies are well-contained and the deployment process is streamlined.

### Redis Caching

I decided to integrate Redis as an in-memory cache for the latest sensor readings. This choice improves the API's response time for frequently requested data by storing it in memory, reducing the load on the MongoDB database.

### FastAPI for API Endpoints

I opted to use FastAPI to build the API endpoints. FastAPI's asynchronous capabilities and auto-generation of OpenAPI documentation make it a powerful choice for quickly creating and documenting APIs.

## Challenges and Solutions
### Challenge: Connecting to the MQTT Broker
Connecting the python paho-mqtt client to the Mosquitto broker in the publisher and subscriber files return an error code 5 which represents Unauthorized access.

**solution:** I used a `mosquitto.conf` file to configure the mosquitto broker to authorize access. Currently, I've authorized access to the broker without user and password but we can add an user and password in the config file and use these credentials to connect to the broker.

### Challenge: Data Retrieval Performance

One challenge I encountered was optimizing the performance of data retrieval from the MongoDB database for the FastAPI endpoints. Frequent database queries for the same data were affecting response times.

**Solution:** I implemented a caching mechanism using Redis. Whenever a request for sensor data is made, the system first checks the Redis cache. If the data is found, it's returned quickly. If not, the data is fetched from MongoDB, stored in Redis, and then returned. This significantly improved response times for frequently requested data.

### Challenge: Docker Networking and Service Connectivity

Getting the various Docker containers (MQTT broker, MQTT publisher, MQTT subscriber, FastAPI, MongoDB, and Redis) to communicate effectively was challenging due to the different services and networks involved.

**Solution:** I created a custom Docker network named `containernetwork` and assigned all services to it. This allowed us to refer to service names as hostnames within the network, making service-to-service communication straightforward. It also provided better isolation and organization of services.

### Challenge: Testing and Debugging

Testing and debugging Dockerized applications presented challenges, especially in isolating issues that might arise in different containers.

**Solution:** I utilized Docker's logging capabilities to capture container logs, both standard output and standard error, to debug issues. I also used the `docker exec` command to log into containers and inspect their environments interactively.
