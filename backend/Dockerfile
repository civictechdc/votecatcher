FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./

RUN uv sync --dev

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py", "--env", "local"]
