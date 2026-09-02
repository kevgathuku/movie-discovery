FROM python:3.14-slim

RUN pip install --no-cache-dir uv

ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --extra dev

COPY . .

RUN chmod +x docker-entrypoint.sh

ENV UV_NO_SYNC=1
ENV PYTHONPATH=/app

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
