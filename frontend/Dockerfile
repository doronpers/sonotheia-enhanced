# Stage 1: Build the React Application
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies (use correct lockfile)
COPY package.json yarn.lock ./
# If you used npm, you would prefer package-lock.json
# COPY package.json package-lock.json ./ 
RUN yarn install --frozen-lockfile

# Copy source code and build
COPY . .
RUN yarn build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built artifacts from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
