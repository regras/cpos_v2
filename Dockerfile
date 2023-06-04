# syntax=docker/dockerfile:1

# FROM ubuntu:22.04
FROM mwalbeck/python-poetry:1.5-3.10
WORKDIR /cpos
COPY . /cpos

RUN poetry install

CMD ["/bin/bash"]
