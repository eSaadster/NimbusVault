FROM node:18-alpine

WORKDIR /app

# Use admin-ui/package.json if this is specifically for the admin UI
COPY admin-ui/package*.json ./
RUN npm install

# Copy the full admin-ui directory contents
COPY admin-ui/ ./

RUN npm run build

# Use port 3001 (assuming health check path is correct and preferred)
EXPOSE 3001
CMD ["npm", "start"]

# Add a health check endpoint
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3001/api/health/ready || exit 1
