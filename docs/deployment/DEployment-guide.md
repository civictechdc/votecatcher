version: "3.8"

services:
  fastapi:
    image: python:3.12-slim
    container_name: votecatcher
    build: .
    command: uvicorn app.main:app.api --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql://votecatcher:votecatcher@db/votecatcher:5432
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      # LLM Provider (set at least one, but for MVP, use OpenAI)
      # GEMINI_API_KEY=${GEMINI_API_KEY}
      # Mistral_API_KEY=${MISTRAL_API_KEY}

    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./env:/var/lib/votecatcher/data
      - ./env-file:/var/lib/votecatcher/.env

    networks:
      app_network:
        external_network:
        db_network

    restart: unless-stopped
      web:
        restart: on-failure
      test: ["CMD-SHELL", "uvicorn app.main:app.api --timeout 30"]
      - postgres
        condition: service_healthy

  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      - POSTGRES_DB
      - POSTGRES_USER
      - POSTGRES_PASSWORD

  nginx:
    image: nginx:1.25-alpine
    container_name: nginx
    ports:
      - "8000:8000"
      - "5173:5173"
    volumes_from:
      - .:/nginx.conf.d:/etc/nginx/conf.d
    environment:
      - UPSTREAM_URL: http://votecatcher-backend:8000
    depends_on:
      - frontend
        image: votecatcher-frontend
        build: .
        ports:
          - "5173:5173"
    command: npm run build
    command: npm run preview

    volumes_from:
      - .:/usr/src/app/dist:/var/www/html:ro

  upstream_votecatcher-backend {
    server {
      listen 8000;
      server_name _ votecatcher-backend;
      location /etc/nginx/votecatcher-backend.conf.d/ {
        proxy_set_header X-Real-IP $true;
        proxy_set_header Host $host;
        proxy_redirect off;
      }

      location / {
        root   /usr/share/nginx/html;
        index index.html index.html;
        try_files $uri /$uri/ = rewrite ^([^/]*)$ break;
        }
      }
    }
  }
