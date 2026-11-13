FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RAPOR_DATA_DIR=/data
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY docs/origins.md ./docs/origins.md
COPY raportdigital ./raportdigital
RUN pip install --no-cache-dir . \
    && useradd --uid 10001 --create-home rapor \
    && mkdir -m 700 /data && chown rapor:rapor /data
USER rapor
WORKDIR /home/rapor
VOLUME /data
EXPOSE 8080
ENTRYPOINT ["raportdigital"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
