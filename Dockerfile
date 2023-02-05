# syntax=docker/dockerfile:1

FROM python:3.9-alpine

WORKDIR /hoymiles-mqtt

RUN apt-get update && apt-get install -y git
COPY . .
RUN pip3 install -e .

CMD [ "python3", "-m" , "hoymiles_mqtt"]
