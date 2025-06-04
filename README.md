NimbusVault
NimbusVault is a microservices-based media storage application built with Docker Compose. Each service runs in its own container, making the system modular, scalable, and easy to maintain.

🧩 Services
Service	Description	Port
nginx	Reverse proxy for routing requests to internal services	80
gateway	Node.js Express server acting as the API entry point	3000
auth-service	FastAPI service for authentication	8001
upload-service	FastAPI service for uploading files via /upload	8002
metadata-service	FastAPI service storing file metadata in PostgreSQL	8003
storage-service	Internal Python service for handling file storage operations	Internal
admin-ui	Next.js frontend interface for administrators	3001
db	PostgreSQL database initialized with db-init/init.sql	5432


Docker

Docker Compose

Run the Project
bash
Copy
Edit
git clone <repository-url>
cd nimbusvault
docker compose up --build
🌐 Access Points
Access the application via NGINX reverse proxy:

Main Entry (NGINX): http://localhost

Individual services (for debugging/testing):

Gateway: http://localhost:3000

Auth Service: http://localhost:8001

Upload Service: http://localhost:8002

Metadata Service: http://localhost:8003

Admin UI: http://localhost:3001

🧱 Architecture Diagram
pgsql
Copy
Edit
+-------------+
|  Admin UI   | (3001)
+-------------+
      |
      v
+-------------+
|   Gateway   | (3000)
+-------------+
      |
      v
+-------------+
|   NGINX     | (80)
+-------------+
   /    |    \
  v     v     v
Auth  Upload  Metadata
8001   8002     8003
                |
                v
         +-------------+
         | PostgreSQL  | (5432)
         +-------------+
                |
                v
         +-------------+
         | Storage Svc | (internal)
         +-------------+