# Estagio 1: Compilacao da aplicacao Angular
FROM node:22-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build -- --configuration production

# Estagio 2: Servidor Web Nginx
FROM nginx:1.27-alpine

# Remove configuracao default
RUN rm -rf /etc/nginx/conf.d/*

# Copia configuracao de roteamento SPA e proxy reverso
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copia artefatos estaticos gerados no build
COPY --from=builder /app/dist/frontend-init/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
