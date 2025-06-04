# NimbusVault

NimbusVault is a microservices-based media storage application built with Docker Compose. Each service is isolated in its own container to keep the stack modular and easy to maintain.

## Services
- **gateway** – Node.js Express entry point for all API traffic.
- **auth-service** – FastAPI service handling authentication.
- **upload-service** – FastAPI service for receiving uploads.
- **storage-service** – Utility module for storing files (no HTTP interface).
- **metadata-service** – FastAPI service that stores metadata in PostgreSQL.
- **admin-ui** – Next.js interface for administrators.
- **db** – PostgreSQL database initialized with `db-init/init.sql`.

## Setup
```bash
git clone <repository-url>
cd NimbusVault/nimbusvault
docker-compose up --build
```

## Endpoints and Ports
| Service           | Endpoint | Port |
|-------------------|---------|------|
| gateway           | `/`     | 3000 |
| auth-service      | `/`     | 8001 |
| upload-service    | `/`     | 8002 |
| metadata-service  | `/`     | 8003 |
| admin-ui          | `/`     | 3001 |
| db                | n/a     | 5432 |
| storage-service   | n/a     | internal |

Services can be accessed via `http://localhost:<port>`.

## Architecture
```
      +-------------+
      |  Admin UI   | (3001)
      +-------------+
             |
             v
      +-------------+
      |   Gateway   | (3000)
      +-------------+
       /     |     \
      v      v      v
 auth-svc upload-svc metadata-svc
  (8001)    (8002)      (8003)
                        |
                        v
                   PostgreSQL (5432)
                        |
                        v
                   storage-svc
```
