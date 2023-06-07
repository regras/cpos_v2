# syntax=docker/dockerfile:1

FROM mwalbeck/python-poetry:1.5-3.11
WORKDIR /cpos
COPY . /cpos

VOLUME ["/cpos"]

RUN poetry install

CMD ["/bin/bash"]
