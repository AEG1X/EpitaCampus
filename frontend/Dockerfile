# 1) Compilation du site SvelteKit
FROM node:24-slim AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

# 2) Caddy sert les fichiers statiques et redirige /api vers le backend
FROM caddy:2
COPY --from=build /app/build /srv
