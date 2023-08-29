# cpos_v2
A new and refactored version of CPoS.

## Dependencies

- Docker 24.0
- Docker Compose 2.20
- Poetry 1.6.1

## Building

First off, install the project with

```
$ poetry install
```

Poetry automatically creates [isolated virtual environments](https://realpython.com/python-virtual-environments-a-primer/) for every project (this avoids all sorts of nasty problems with environment variables). **It is strongly recommended that you use a virtualenv when working on this project**. To spawn a shell within the project's virtualenv, run:

```
$ poetry shell
```

## Running

To launch the demo blockchain:

```
$ docker compose up
```
