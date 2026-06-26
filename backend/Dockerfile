FROM python:3.13-slim

WORKDIR /app

ARG APT_CACHE_BUST=manual
RUN apt-get update && \
    echo "APT cache bust: ${APT_CACHE_BUST}" && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.11.13

COPY pyproject.toml uv.lock ./
RUN mkdir -p app && touch app/__init__.py
RUN uv sync --no-dev --frozen

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py", "--env", "local"]
