# cpos_v2
A new and refactored version of CPoS.

## Run with Docker

### Running a beacon

Run the following to build+run the Docker image, as well as spawn a beacon instance:

```
$ sudo docker compose run beacon
```

Now, inside the container, run the following to configure the environment:

```
# poetry shell
```

## Requirements
We use [Poetry](https://python-poetry.org/docs/) to build the project, manage dependencies and run unit tests. To install it on Linux/WSL, run

```
$ curl -sSL https://install.python-poetry.org | python3 -
```

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

You can run code within any file in the project just like you would with any regular Python script:

```
$ python cpos/<path-to-file>/<file>.py
```

We use [pytest](https://docs.pytest.org/en/7.3.x/) for unit testing. To run all tests, do

```
$ pytest
```

You can also run specific tests with

```
$ pytest test/<path-to-test>
```
