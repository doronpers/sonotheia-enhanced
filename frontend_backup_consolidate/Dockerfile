# Stage 1: Build the React Application
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies (use npm)
COPY package.json ./
# Generate package-lock.json if missing and install dependencies
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built artifacts from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
