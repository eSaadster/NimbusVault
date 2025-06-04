FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3001
CMD ["npm", "start"]
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3001/api/health/ready || exit 1
