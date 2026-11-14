# syntax=docker/dockerfile:1

# export runtime dependencies in versions pinned by poetry.lock
FROM python:3.12-slim AS requirements

RUN pip3 install --no-cache-dir poetry-plugin-export
COPY pyproject.toml poetry.lock ./
RUN poetry export --only main --output /requirements.txt

FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1
ENV CACHE_FILE=/data/cache.json

WORKDIR /hoymiles-mqtt

COPY --from=requirements /requirements.txt .
RUN pip3 install --no-cache-dir --require-hashes -r requirements.txt

COPY . .
RUN pip3 install --no-cache-dir --no-deps .

VOLUME /data

CMD [ "python3", "-m" , "hoymiles_mqtt"]
