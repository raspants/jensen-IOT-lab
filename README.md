# Jensen IoT Platform

A containerized IoT platform for collecting, validating, storing, and retrieving sensor measurements.

The system consists of a Flask API, PostgreSQL database, Redis cache, and a sensor simulator. Docker Compose is used for local development, while Kubernetes manifests are included for deploying the API.

## Table of Contents

* [Technologies](#technologies)
* [Getting Started](#getting-started)

  * [Prerequisites](#prerequisites)
  * [Run the application](#run-the-application)
  * [Check the application](#check-the-application)
* [API](#api)
* [Validation](#validation)
* [Database](#database)
* [Redis Cache](#redis-cache)
* [Sensor Simulator](#sensor-simulator)
* [Testing](#testing)
* [Continuous Integration](#continuous-integration)
* [Kubernetes](#kubernetes)
* [Documentation](#documentation)
* [Stopping the Application](#stopping-the-application)

## Technologies

| Technology     | Purpose                       |
| -------------- | ----------------------------- |
| Python         | Application and simulator     |
| Flask          | REST API                      |
| PostgreSQL 16  | Persistent data storage       |
| Redis 7        | Latest-measurement cache      |
| Docker Compose | Local development environment |
| Kubernetes     | API deployment                |
| Pytest         | Automated testing             |
| GitHub Actions | Continuous integration        |

## Getting Started

### Prerequisites

* Docker
* Docker Compose
* Git
* Minikube
* Kubernetes and `kubectl` if using the Kubernetes deployment

### Run the application

From the project root:

```bash
docker compose up --build -d
```

Check the containers:

```bash
docker compose ps
```

The API is available at:

```text
http://localhost:5001
```

### Check the application

The API health endpoint can be tested with:

```bash
curl http://localhost:5001/health
```

View API logs with:

```bash
docker compose logs api
```

The simulator can be monitored with:

```bash
docker compose logs -f simulator
```

## API

The Flask API is available at:

```text
http://localhost:5001/
```

Endpoints can be accessed by appending the endpoint path to the base URL.

For example:

```bash
curl http://localhost:5001/health
```

### Endpoints

| Method | Endpoint                            | Description                                 |
| ------ | ----------------------------------- | ------------------------------------------- |
| GET    | `/`                                 | API landing endpoint                        |
| GET    | `/health`                           | Checks that the API is running              |
| GET    | `/devices`                          | Retrieves registered sensors                |
| GET    | `/measurements`                     | Retrieves stored measurements               |
| POST   | `/measurements`                     | Validates and stores a new measurement      |
| GET    | `/devices/<device_id>/measurements` | Retrieves measurement history               |
| GET    | `/devices/<device_id>/latest`       | Retrieves the latest measurement            |
| GET    | `/count-readings`                   | Returns the total number of measurements    |
| GET    | `/average-temp`                     | Returns the average temperature             |
| GET    | `/last-24h`                         | Returns measurements from the last 24 hours |
| GET    | `/statistics`                       | Optional challenge endpoint  (not built)    |

The `/statistics` endpoint is currently not implemented and returns `501 Not Implemented`.

### Create a measurement

Measurements can be submitted as JSON:

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

A successful request returns `201 Created`.

Invalid data returns `400 Bad Request`, while requests for unknown devices through device-specific GET endpoints return `404 Not Found`.

## Validation

Incoming measurements are validated before being stored.

Required fields:

* `deviceId`
* `temperature`

Optional fields:

* `humidity`
* `battery`

The API checks that temperature and humidity are numbers and that battery is an integer.

Validation is implemented in:

```text
api/validation.py
```

The simulator also sends intentionally invalid data from `sensor-003` to test the validation logic.

## Database

PostgreSQL stores the persistent measurement data.

Database initialization is handled by:

```text
database/init.sql
```

Database operations are implemented in:

```text
api/db.py
```

### Access PostgreSQL

Open a PostgreSQL shell with:

```bash
docker compose exec db psql -U student -d jensen_iot
```

Some useful queries:

```sql
SELECT COUNT(*) AS total_measurements
FROM measurements;
```

```sql
SELECT ROUND(AVG(temperature), 2) AS average_temperature
FROM measurements;
```

```sql
SELECT *
FROM measurements
WHERE created_at >= NOW() - INTERVAL '24 hours';
```

Exit with:

```sql
\q
```

## Redis Cache

Redis caches the latest measurement for each device.

Cache keys use the format:

```text
latest:<device_id>
```

For example:

```text
latest:sensor-001
```

The latest-measurement endpoint uses a **cache-aside** strategy:

1. Check Redis for the latest measurement.
2. On a cache hit, return the cached value.
3. On a cache miss, retrieve the value from PostgreSQL.
4. Store the result in Redis.
5. Return the measurement.

PostgreSQL remains the persistent source of truth.

## Sensor Simulator

The simulator is located in:

```text
simulator/simulator.py
```

It sends measurements to the API approximately every five seconds.

| Sensor       | Temperature |
| ------------ | ----------- |
| `sensor-001` | 20–23 °C    |
| `sensor-002` | 18–21 °C    |
| `sensor-003` | 22–25 °C    |

Each sensor sends:

* device ID
* temperature
* humidity
* battery

`sensor-003` intentionally produces invalid temperature data at times, either by sending `"ERROR"` or omitting the temperature field.

## Testing

The project uses Pytest.

The current tests cover:

* valid measurements
* missing device ID
* missing temperature
* invalid temperature
* invalid humidity
* invalid battery

Run the tests with:

```bash
docker compose exec api python -m pytest -q
```

## Continuous Integration

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

The workflow runs on pushes and pull requests.

It:

1. Installs the API dependencies.
2. Runs the Pytest suite.
3. Builds the API Docker image.

The Docker image is built with:

```bash
docker build -t jensen-iot-api:ci ./api
```

## Kubernetes

Kubernetes manifests are located in:

```text
k8s/
```

### Start Minikube

Start the local Kubernetes cluster using Docker:

```bash
minikube start --driver=docker
```

Build the API image directly inside Minikube:

```bash
minikube image build -t jensen-iot-api:lab ./api
```

The API deployment uses:

* 3 replicas
* port `5000`
* image `jensen-iot-api:lab`
* `/health` readiness probe

The service exposes the API through NodePort `30080`.

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

The supplied Kubernetes manifests deploy the API only. PostgreSQL and Redis are provided through Docker Compose.

### Scaling

The API deployment can be scaled up or down depending on the required number of replicas.

Scale the API to 5 replicas:

```bash
kubectl scale deployment jensen-iot-api --replicas=5
```

Scale it back down to 1 replica:

```bash
kubectl scale deployment jensen-iot-api --replicas=1
```

Check the current number of replicas:

```bash
kubectl get deployments
```

The default deployment is configured with 3 replicas.


## Documentation

Additional project documentation:

* [Architecture](docs/architecture.md)
* [Lab Guide](docs/lab-guide.md)
* [Reflection](docs/reflection.md)

## Stopping the Application

### Docker Compose

Stop the running containers:

```bash
docker compose stop
```

Stop and remove the containers and network:

```bash
docker compose down
```

To rebuild and start the application again:

```bash
docker compose up --build -d
```

Removing Docker volumes will also remove the stored PostgreSQL data.

### Minikube

To stop the Minikube cluster without deleting it:

```bash
minikube stop
```

To start the cluster again:

```bash
minikube start --driver=docker
```

To remove the Minikube cluster completely:

```bash
minikube delete
```

If the Kubernetes resources should be removed while keeping the Minikube cluster:

```bash
kubectl delete -f k8s/services.yaml
kubectl delete -f k8s/deployment.yaml
```

