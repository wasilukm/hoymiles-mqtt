# syntax=docker/dockerfile:1

FROM python:3-slim

WORKDIR /hoymiles-mqtt

COPY . .
RUN pip3 install -e .

CMD [ "python3", "-m" , "hoymiles_mqtt"]
