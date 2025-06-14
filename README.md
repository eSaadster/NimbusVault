NimbusVault
NimbusVault is a microservices-based media storage application built with Docker Compose. Each service runs in its own container, making the system modular, scalable, and easy to maintain.

🧩 Services Overview
Service	Description	Port
nginx	Reverse proxy for routing requests	80
gateway	Node.js Express entry point for all API traffic	3000
auth-service	FastAPI service handling authentication	8001
upload-service	FastAPI service for receiving uploads	8002
metadata-service	FastAPI service storing metadata in PostgreSQL	8003
storage-service	Internal FastAPI service for handling file storage	Internal
storage-init	One-shot service initializing the directory structure	n/a
admin-ui	Next.js web interface for administrators	3001
db	PostgreSQL database initialized with init.sql	5432

🚀 Setup
bash
Copy
Edit
git clone <repository-url>
cd nimbusvault
docker compose up --build
🌐 Access Points
All services are accessible via http://localhost:<port> for testing and development.

NGINX Proxy: http://localhost

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
      |    NGINX    | (80)
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
                    storage-service
🗂️ Storage Layout
The storage-init service sets up a persistent directory tree under /vault-storage, modeled after a NextCloud-compatible layout:

bash
Copy
Edit
/vault-storage/
├── files/              # Main file storage
├── users/
│   ├── admin/
│   ├── user1/
│   └── user2/
├── shared/             # Public/shared files
├── trash/              # Recycle bin
└── external/
    └── nimbusvault/    # Link to NimbusVault files
This structure enables compatibility with external tools and services expecting a NextCloud-style file system.