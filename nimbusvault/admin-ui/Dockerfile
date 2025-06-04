FROM node:18-alpine
WORKDIR /app
COPY admin-ui/package*.json ./
RUN npm install
COPY admin-ui/ ./
RUN npm run build
EXPOSE 3001
CMD ["npm", "start"]
