# NimbusVault

NimbusVault is a Docker-based microservices architecture.

## Services
- **gateway**: Node.js Express server acting as entrypoint.
- **auth-service**: FastAPI for authentication.
- **upload-service**: FastAPI for file uploads. Exposes `POST /upload` for uploading files.
- **storage-service**: Python service handling storage utilities.
- **metadata-service**: FastAPI service storing metadata in PostgreSQL.
- **admin-ui**: Next.js frontend.
- **db**: PostgreSQL database initialized with `db-init/init.sql`.

## Getting Started

Ensure you have Docker and Docker Compose installed.

```bash
cd nimbusvault
docker compose up --build
```

## Ports
- Gateway: `3000`
- Auth Service: `8001`
- Upload Service: `8002`
- Metadata Service: `8003`
- Admin UI: `3001`
- PostgreSQL: `5432`

Access the services via `http://localhost:<port>`.
