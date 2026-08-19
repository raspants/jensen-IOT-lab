# Jensen IoT Platform

A containerized IoT platform for collecting, validating, storing, caching, and retrieving sensor measurements. The project combines a Flask REST API with PostgreSQL, Redis, a sensor simulator, Docker Compose, Kubernetes, automated tests, and GitHub Actions CI.

## Overview

The Jensen IoT Platform simulates a small IoT environment where sensors periodically send temperature, humidity, and battery measurements to a Flask API.

The API validates incoming data, stores valid measurements in PostgreSQL, and uses Redis to cache the latest measurement for each device.

The project also includes automated tests, a Docker-based development environment, a GitHub Actions CI pipeline, and Kubernetes manifests for running multiple API replicas.
## Table of Contents

- [Overview](#overview)
- [Technologies](#technologies)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Start the application](#start-the-application)
  - [Check the API](#check-the-api)
  - [View logs](#view-logs)
- [REST API](#rest-api)
  - [Endpoint overview](#endpoint-overview)
  - [Example requests](#example-requests)
  - [Create a measurement](#create-a-measurement)
- [Data Validation](#data-validation)
- [PostgreSQL](#postgresql)
  - [Access PostgreSQL](#access-postgresql)
  - [Useful SQL queries](#useful-sql-queries)
- [Redis Cache](#redis-cache)
  - [Cache-aside pattern](#cache-aside-pattern)
- [Sensor Simulator](#sensor-simulator)
  - [Invalid sensor data](#invalid-sensor-data)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [Kubernetes](#kubernetes)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
  - [API dependencies](#api-dependencies)
  - [Simulator dependency](#simulator-dependency)
- [Documentation](#documentation)
- [Stopping the Application](#stopping-the-application)
- [Resetting the Environment](#resetting-the-environment)
- [Project Summary](#project-summary)

### Main data flow

```text
Sensor simulator
       |
       v
   Flask API
       |
       v
  Validation
       |
       +----------------+
       |                |
       v                v
 PostgreSQL          Redis cache
       |                |
       +-------+--------+
               |
               v
        API response
```

For a more detailed view of the system architecture, see [Architecture Documentation](docs/architecture.md).

## Technologies

| Technology     | Purpose                               |
| -------------- | ------------------------------------- |
| Python         | Application and simulator development |
| Flask          | REST API                              |
| PostgreSQL 16  | Persistent data storage               |
| Redis 7        | Latest-measurement cache              |
| Docker Compose | Local multi-container environment     |
| Kubernetes     | API deployment and service exposure   |
| Pytest         | Automated testing                     |
| GitHub Actions | Continuous integration                |

## Getting Started

### Prerequisites

Make sure the following tools are installed:

* Docker
* Docker Compose
* Git
* Kubernetes and `kubectl` if you want to use the Kubernetes deployment

### Start the application

From the project root, build and start the containers:

```bash
docker compose up --build -d
```

Check the running containers:

```bash
docker compose ps
```

The Flask API is available at:

```text
http://localhost:5001
```

The API listens on port `5000` inside the container, which is mapped to port `5001` on the host.

### Check the API

Check that the API is running:

```bash
curl http://localhost:5001/health
```

The root endpoint can also be accessed with:

```bash
curl http://localhost:5001/
```

### View logs

View API logs:

```bash
docker compose logs api
```

Follow the simulator logs:

```bash
docker compose logs -f simulator
```

The simulator sends measurements approximately every five seconds.

## REST API

The Flask application provides endpoints for devices, measurements, statistics, and health checks.

The Flask API is available at: ```
 http://localhost:5001/

For example, the health endpoint request can be accessed with: curl http://localhost:5001/health

### Endpoint overview

| Method | Endpoint                            | Description                                                          |
| ------ | ----------------------------------- | -------------------------------------------------------------------- |
| GET | `/` | API landing endpoint |
| GET | `/health` | Checks that the API is running |
| GET | `/devices` | Retrieves registered sensors |
| GET | `/measurements` | Retrieves stored measurements |
| POST | `/measurements` | Validates and stores a new measurement |
| GET | `/devices/<device_id>/measurements` | Retrieves measurement history for a sensor |
| GET | `/devices/<device_id>/latest` | Retrieves the latest measurement for a sensor |
| GET | `/count-readings` | Returns the total number of measurements |
| GET | `/average-temp` | Returns the average temperature |
| GET | `/last-24h` | Returns measurements from the last 24 hours |


### Create a measurement

A valid measurement can be submitted using:

```bash
curl -X POST http://localhost:5001/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "sensor-001",
    "temperature": 21.5,
    "humidity": 45,
    "battery": 92
  }'
```

A successful request returns:

```text
201 Created
```

Invalid measurement data returns:

```text
400 Bad Request
```

An unknown device also returns:

```text
400 Bad Request
```

Requests for an unknown device through the device-specific GET endpoints return:

```text
404 Not Found
```

## Data Validation

Incoming measurements are validated before they are stored.

The API requires:

* `deviceId`
* `temperature`

The following fields are optional:

* `humidity`
* `battery`

The expected data types are:

| Field         | Expected value              |
| ------------- | --------------------------- |
| `deviceId`    | Non-empty device identifier |
| `temperature` | Number                      |
| `humidity`    | Number                      |
| `battery`     | Integer                     |

The validation logic is implemented in:

```text
api/validation.py
```

Invalid input is rejected before it is inserted into PostgreSQL.

For example, a missing temperature or a temperature value such as `"ERROR"` results in a `400 Bad Request`.

## PostgreSQL

PostgreSQL is used as the persistent database for the IoT measurements.

The database initialization script is located at:

```text
database/init.sql
```

Database-related functions are implemented in:

```text
api/db.py
```

The database layer handles:

* database connections
* device lookup
* retrieving devices
* retrieving measurements
* checking whether a device exists
* retrieving the latest measurement
* retrieving measurements for a specific device
* inserting measurements
* counting measurements
* calculating average temperature
* retrieving measurements from the last 24 hours

### Access PostgreSQL

Open a PostgreSQL shell inside the database container:

```bash
docker compose exec db psql -U student -d jensen_iot
```

### Useful SQL queries

Count all measurements:

```sql
SELECT COUNT(*) AS total_measurements
FROM measurements;
```

Calculate the average temperature:

```sql
SELECT ROUND(AVG(temperature), 2) AS average_temperature
FROM measurements;
```

Retrieve measurements from the last 24 hours:

```sql
SELECT *
FROM measurements
WHERE created_at >= NOW() - INTERVAL '24 hours';
```

The `created_at` column is used to determine whether a measurement belongs to the last 24 hours.

Exit the PostgreSQL shell with:

```sql
\q
```

## Redis Cache

Redis is used to cache the latest measurement for each device.

The cache implementation is located in:

```text
api/cache.py
```

Cache keys use the following format:

```text
latest:<device_id>
```

Examples include:

```text
latest:sensor-001
latest:sensor-002
latest:sensor-003
```

### Cache-aside pattern

The `/devices/<device_id>/latest` endpoint uses a cache-aside strategy.

The request flow is:

1. Check that the device exists.
2. Look for the latest measurement in Redis.
3. If the measurement is found in Redis, return it.
4. If Redis has no cached value, query PostgreSQL.
5. If PostgreSQL has no measurement, return `404 Not Found`.
6. Store the PostgreSQL result in Redis.
7. Return the measurement.

This means PostgreSQL remains the persistent source of truth while Redis can provide faster access to frequently requested latest readings.

When a new measurement is successfully submitted, the API also updates the Redis entry for that device.

## Sensor Simulator

The sensor simulator is located in:

```text
simulator/simulator.py
```

It uses the `requests` library to send measurements to the API approximately every five seconds.

The simulator contains three sensors:

| Sensor       | Temperature range |
| ------------ | ----------------- |
| `sensor-001` | 20–23 °C          |
| `sensor-002` | 18–21 °C          |
| `sensor-003` | 22–25 °C          |

Each simulated sensor sends:

* device ID
* temperature
* humidity
* battery

### Invalid sensor data

`sensor-003` intentionally generates invalid temperature data around 15% of the time.

The invalid data can contain:

```text
"ERROR"
```

or omit the `temperature` field.

This behavior is intentional and is used to test the API's validation and error handling.

View the simulator output with:

```bash
docker compose logs -f simulator
```

## Testing

The project uses Pytest for automated testing.

The current tests cover:

1. Valid measurement
2. Missing device ID
3. Missing temperature
4. Invalid temperature type
5. Invalid humidity type
6. Invalid battery type

Run the test suite with:

```bash
docker compose exec api python -m pytest -q
```

The current result is:

```text
6 passed in 0.01s
```

## Continuous Integration

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

The CI workflow runs on:

* pushes
* pull requests

The workflow performs the following steps:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Installs the dependencies from `api/requirements.txt`.
4. Runs the Pytest test suite.
5. Builds the API Docker image.

The Docker image is built using:

```bash
docker build -t jensen-iot-api:ci ./api
```

This provides an automated check that the application tests pass and that the API image can be built successfully.

## Kubernetes

Kubernetes configuration is located in:

```text
k8s/
```

The API deployment is configured with:

* 3 replicas
* image `jensen-iot-api:lab`
* container port `5000`
* `APP_VERSION=lab`
* readiness probe using `/health`

The Kubernetes service exposes port `80` and forwards traffic to port `5000`.

The service uses:

```text
NodePort: 30080
```

### Deploy the API

Apply the deployment:

```bash
kubectl apply -f k8s/deployment.yaml
```

Apply the service:

```bash
kubectl apply -f k8s/services.yaml
```

Check the deployment:

```bash
kubectl get deployments
```

Check the pods:

```bash
kubectl get pods
```

Check the service:

```bash
kubectl get services
```

The supplied Kubernetes manifests deploy the API only. PostgreSQL and Redis are not included in these Kubernetes manifests and are provided by the Docker Compose environment.

## Configuration

The API uses environment variables for its database, Redis, and application configuration.

Important variables include:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
REDIS_HOST
REDIS_PORT
APP_VERSION
```

Docker Compose provides the service configuration required for the local containerized environment.

## Dependencies

### API dependencies

The API uses:

```text
Flask==3.1.1
psycopg2-binary==2.9.10
redis==6.2.0
pytest==8.4.1
```

These dependencies are defined in:

```text
api/requirements.txt
```

### Simulator dependency

The simulator uses:

```text
requests==2.32.4
```

The dependency is defined in:

```text
simulator/requirements.txt
```

## Documentation

Additional documentation is available in the `docs/` directory.

* [Architecture Documentation](docs/architecture.md) — detailed system architecture
* [Lab Guide](docs/lab-guide.md) — project and lab-related instructions
* [Reflection](docs/reflection.md) — project reflection

The architecture is kept in a separate document so that this README can focus on setup, usage, implementation details, and development.

## Stopping the Application

Stop the running containers without removing them:

```bash
docker compose stop
```

Stop and remove the containers and network:

```bash
docker compose down
```

To rebuild the application after changing code or dependencies:

```bash
docker compose up --build -d
```

## Resetting the Environment

To recreate the Compose environment:

```bash
docker compose down
docker compose up --build -d
```

If Docker volumes are removed as part of a reset, PostgreSQL data will also be deleted and the database will be initialized again from `database/init.sql`.

Be careful when removing volumes because persisted measurements will be lost.

## Project Summary

The Jensen IoT Platform brings together several components into one containerized IoT system:

* simulated sensors generate measurements
* Flask provides the REST API
* validation rejects malformed measurements
* PostgreSQL provides persistent storage
* Redis caches the latest measurement for each device
* Docker Compose runs the local environment
* Pytest verifies the validation logic
* GitHub Actions automates testing and image builds
* Kubernetes provides a replicated API deployment

The project demonstrates how an IoT backend can combine an API, persistent storage, caching, automated testing, containerization, and deployment tooling into a single reproducible system.

