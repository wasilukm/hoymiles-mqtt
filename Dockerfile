# syntax=docker/dockerfile:1

# export runtime dependencies in versions pinned by poetry.lock
FROM python:3.12-slim AS requirements

RUN pip3 install --no-cache-dir poetry==2.5.1 poetry-plugin-export==1.10.1
COPY pyproject.toml poetry.lock ./
RUN poetry export --only main --output /requirements.txt

FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1
ENV CACHE_FILE=/data/cache.json
ENV HEALTH_FILE=/tmp/hoymiles-mqtt.health

WORKDIR /hoymiles-mqtt

COPY --from=requirements /requirements.txt .
RUN pip3 install --no-cache-dir --require-hashes -r requirements.txt

COPY . .
RUN pip3 install --no-cache-dir --no-deps .

# run as a regular user, owning the data directory (a new named volume gets the same owner)
RUN adduser -D -H -u 1000 hoymiles && mkdir /data && chown hoymiles /data
USER hoymiles
VOLUME /data

# unhealthy when no data was published to MQTT during the last 3 query periods
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=1 CMD python3 -c "import os, sys, time; \
period = int(os.environ.get('QUERY_PERIOD', '60')); \
sys.exit(0 if time.time() - os.path.getmtime(os.environ['HEALTH_FILE']) < 3 * period + 30 else 1)"

CMD [ "python3", "-m" , "hoymiles_mqtt"]
