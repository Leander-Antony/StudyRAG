# Use Node.js lightweight base for building (if needed)
FROM node:20-alpine AS builder

WORKDIR /app
COPY . .

# Optional: Add any build steps if needed in the future
# For now, static files are copied as-is

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy frontend files
COPY --from=builder /app /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
