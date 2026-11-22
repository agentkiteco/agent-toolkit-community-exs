FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_HOST=0.0.0.0 APP_PORT=8080
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p /app/private && chown app:app /app/private
COPY . /app
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python", "-B", "cloud_entrypoint.py"]
