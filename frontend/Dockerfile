# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Use lockfile if present for reproducible builds
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN \
  if [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
  elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
  else npm ci; fi

# Copy source and build
COPY . .
# Ensure vite.svg exists if referenced at /vite.svg; or remove the reference in your app.
RUN mkdir -p public && (test -f public/vite.svg || echo '<svg xmlns="http://www.w3.org/2000/svg"/>' > public/vite.svg)
# Accept build argument
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Then build
RUN npm run build

# Production stage
FROM nginx:1.27-alpine
WORKDIR /usr/share/nginx/html

# SSL trust roots for HTTPS proxying (coding standard)
RUN apk add --no-cache ca-certificates && update-ca-certificates

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Ensure only our config is present; remove stock configs and templates
RUN rm -f /etc/nginx/conf.d/*.conf && rm -rf /etc/nginx/templates

# Copy nginx config and entrypoint
# Ship our config as default.conf so the stock entrypoint scripts only process our file
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
