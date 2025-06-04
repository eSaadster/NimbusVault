NimbusVault is a microservices-based media storage application built with Docker Compose. Each service runs in its own container, making the system modular, scalable, and easy to maintain.

Services
gateway – Node.js Express server acting as the entry point for all API traffic (Port: 3000).

auth-service – FastAPI service handling user authentication (Port: 8001).

upload-service – FastAPI service exposing POST /upload for file uploads (Port: 8002).

metadata-service – FastAPI service for storing file metadata in PostgreSQL (Port: 8003).

storage-service – Python utility module for handling file system or cloud storage (Internal only).

admin-ui – Next.js frontend interface for administrators (Port: 3001).

db – PostgreSQL database initialized with db-init/init.sql (Port: 5432, internal).

Getting Started
Make sure you have Docker and Docker Compose installed on your machine.

Run the Project
bash
Copy
Edit
git clone <repository-url>
cd nimbusvault
docker-compose up --build
Once the services are running, you can access them at:

Service	Endpoint	Port
Gateway	http://localhost:3000	3000
Auth Service	http://localhost:8001	8001
Upload Service	http://localhost:8002	8002
Metadata Service	http://localhost:8003	8003
Admin UI	http://localhost:3001	3001
DB	n/a (internal)	5432
Storage Service	n/a (internal only)	n/a

Architecture Diagram
plaintext
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