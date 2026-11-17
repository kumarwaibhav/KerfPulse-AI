FROM node:22-alpine AS frontend
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 app
COPY pdm/ ./pdm/
COPY --from=frontend /web/dist ./web/dist
COPY artifacts/nested-workpiece/ ./artifacts/nested-workpiece/
COPY artifacts/engineering-release/ ./artifacts/engineering-release/
COPY data/FeatureAndMetadata_Milling.csv ./data/FeatureAndMetadata_Milling.csv
RUN chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "pdm.api:app", "--host", "0.0.0.0", "--port", "8000"]
