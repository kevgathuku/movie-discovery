FROM python:3.14-slim

RUN pip install --no-cache-dir uv

ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY . .

RUN chmod +x docker-entrypoint.sh

ENV UV_NO_SYNC=1

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
