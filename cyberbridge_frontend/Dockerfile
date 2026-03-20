# Use Node.js as the base image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Set NODE_ENV to production to ensure production build
ENV NODE_ENV=production

# Accept build arguments for production API URL (can be overridden during build)
ARG VITE_PRODUCTION_IP=https://api.cyberbridge.eu
ENV VITE_PRODUCTION_IP=$VITE_PRODUCTION_IP
ARG VITE_BACKEND_PORT=
ENV VITE_BACKEND_PORT=$VITE_BACKEND_PORT

# Build the application for production (skip TypeScript compilation)
RUN npx vite build

# Install serve to serve the built application
RUN npm install -g serve

# Expose port 5173
EXPOSE 5173

# Serve the built application with cache control headers
CMD ["serve", "-s", "dist", "-l", "5173", "--config", "/app/serve.json"]
