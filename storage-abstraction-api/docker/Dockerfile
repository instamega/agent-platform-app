FROM python:3.11-slim
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src ./src

# Install dependencies
RUN pip install --no-cache-dir -e .[dev]

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8080"]