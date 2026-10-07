# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy app
COPY . .

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Run app
CMD ["npm", "start"]
