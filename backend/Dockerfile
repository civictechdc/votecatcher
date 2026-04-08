FROM python:3.13-slim@sha256:7d8999b140f22939451e00b79c0fd86f13d0bc0577b369f8212fce063101fb2a

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.2

COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py
RUN uv sync --dev

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py", "--env", "local"]
