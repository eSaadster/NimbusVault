FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY gateway/package*.json ./
RUN npm install

# Copy service-specific files and shared utilities
COPY gateway/ ./
COPY shared ./shared

# Expose the correct port
EXPOSE 3000

# Start the gateway
CMD ["node", "index.js"]
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/health/ready || exit 1
