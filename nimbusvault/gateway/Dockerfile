FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "index.js"]
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/health/ready || exit 1
