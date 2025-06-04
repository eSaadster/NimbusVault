FROM node:18-alpine

WORKDIR /app

# Use admin-ui/package.json if this is specifically for the admin UI
COPY admin-ui/package*.json ./
RUN npm install

# Copy the full admin-ui directory contents
COPY admin-ui/ ./

RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
