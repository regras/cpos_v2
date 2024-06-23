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
$ docker compose --file docker-compose-local.yml up
```

It will stop running when it gets to round 30. To process the generated data, run (make sure to do it within a Poetry shell environment):

```
$ python demo/process_data.py
```

This will also generate a bunch of images inside `demo/logs`.

## Running with distributed nodes

To run with distributed nodes, you should have a [Docker Swarm set up](https://docs.docker.com/engine/swarm/swarm-tutorial/) with only one Manager. Be sure to have the specified ports open on every node.

After that, you can configure the environment variables on `docker-compose.yml`, such as the variable Tau, the round time, etc.. If you want to copy the log files to process and extract some data, fill the following fields accordingly, so that the data will be sent from the containers to a centralized machine:

1. `SSH_ADDRESS`: user@address of the machine you want to send the data to;
2. `SSH_PASSWORD`: the password for the account;
3. `SCP_PATH`: the full path where you want to send the data to.

Now, with everything configured, you can start the scheme with the following commands:

```
$ docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node
$ docker stack deploy -c docker-compose.yml cpos
```

You have to remove the cpos_node service and then deploy the stack again because the cpos_node has to deploy after the cpos_beacon, and there isn't a way to guarantee the deploy order with Docker Swarm. Otherwise, the nodes wouldn't be able to reach the beacon through its service name. There's a possibility the first command will fail if the cpos_test_network is not created by the time cpos_node or cpos_beacon is deployed. If this happens, run the command again. Unfortunately, we cannot guarantee the order of deploy with Docker Swarm.

If you want to monitor the logs to see what's going on, you can use these commands:

```
$ docker service logs --follow --raw cpos_node
$ docker service logs --follow --raw cpos_beacon
```

The first one refers to the node, and the second one to the beacon. You can press CTRL + C to exit the logs.

Finally, to remove the stack, run the following command:

```
$ docker stack rm cpos
```
