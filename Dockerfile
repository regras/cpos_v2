# syntax=docker/dockerfile:1

FROM mwalbeck/python-poetry:1.5-3.11

WORKDIR /cpos

VOLUME ["/cpos"]

COPY . /cpos

# RUN chown -R root "/cpos"

RUN apt-get update && apt-get install -y default-mysql-server && poetry install

EXPOSE 3306
