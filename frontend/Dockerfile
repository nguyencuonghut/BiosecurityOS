# ── Stage 1: Dependencies ───────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ── Stage 2: Development (Vite dev server + HMR) ───────────
FROM deps AS development
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── Stage 3: Build ──────────────────────────────────────────
FROM deps AS build
COPY . .
RUN npm run build

# ── Stage 4: Production (Nginx serving static files) ────────
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80 443
