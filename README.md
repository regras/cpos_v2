# WTICG SBSeg24 Article

This repository is tied to the article "Evaluating the network traffic on an improved version of the Committeeless Proof-of-Stake blockchain consensus algorithm" published in the Workshop on Scientific Initiation and Undergraduate Works (WTICG), an event integrated with the Brazilian Symposium on Information and Computational Systems Security (SBSeg).

Article's abstract: Blockchain is a powerful way to store and process data in a decentralized manner. Among its consensus algorithms, Committeeless Proof-of-Stake (CPoS) comes as a promising alternative to the better known Proof-of-Work, and Proof-of-Stake, with its reduced power consumption and simpler design without validation committees. However, CPoS is still an emerging algorithm and requires extensive testing to validate its correctness and efficiency. Its first implementation was promising and showed satisfactory results, but it has been  enhanced continuously. This article aims to present the new characteristics added to CPoS and evaluate their impact on the data traffic and on the scheme as a whole.

# Abstract

This repository stores the source code used for collecting the data for the afformentioned article. The file README.md also gives instructions on how to run the simulations and collect the data.

# Running the simulation

## Dependencies

- Docker 24.0
- Docker Compose 2.20
- Poetry 1.6.1

## Building

After cloning the repository, go to the repository directory and install the project with:

```
$ poetry install
```

Poetry automatically creates [isolated virtual environments](https://realpython.com/python-virtual-environments-a-primer/) for every project (this avoids all sorts of nasty problems with environment variables). **It is strongly recommended that you use a virtualenv when working on this project**. To spawn a shell within the project's virtualenv, run:

```
$ poetry shell
```

## Running local network (minimum test)

As a minimum test, you can run all the network's nodes in the local machine. The file docker-compose-local.yml contains environment variables that control various parameters for the consensus mechanism and the network. These values can be changed, just make sure that the value of TOTAL_STAKE corresponds to the total number of nodes in the network (replicas). For this article, the number of replicas of node_dishonest was kept at 0.


You can launch a local network with the command:

```
$ docker compose --file docker-compose-local.yml up
```

It will stop running when it gets to round 30. To process the generated data, run (make sure to do it within a Poetry shell environment):

```
$ python demo/process_data.py
```

This will also generate a bunch of images inside `demo/logs`. 


After the simulation is done, be sure to run the following command to take down the docker nodes (specially before running another simulation).

```
$ docker compose --file docker-compose-local.yml down
```

## Running with distributed nodes

To run with distributed nodes, you should have a [Docker Swarm set up](https://docs.docker.com/engine/swarm/swarm-tutorial/) with only one Manager. Be sure to have the specified ports open on every node.

After that, you can configure the environment variables on `docker-compose.yml`, such as the variable Tau, the round time, etc.. Just make sure that the value of TOTAL_STAKE corresponds to the total number of nodes in the network (replicas). For this article, the number of replicas of node_dishonest was kept at 0. 


If you want to copy the log files to process and extract some data, fill the following fields accordingly, so that the data will be sent from the containers to a centralized machine:

1. `SSH_ADDRESS`: user@address of the machine you want to send the data to;
2. `SSH_PASSWORD`: the password for the account;
3. `SCP_PATH`: the full path where you want to send the data to.

Now, with everything configured, you can start the scheme with the following commands:

```
$ docker stack deploy -c docker-compose.yml cpos ; docker service rm cpos_node cpos_node_dishonest ; docker stack deploy -c docker-compose.yml cpos
```

You have to remove the cpos_node service and then deploy the stack again because the cpos_node / cpos_node_dishonest has to deploy after the cpos_beacon, and there isn't a way to guarantee the deploy order with Docker Swarm. Otherwise, the nodes wouldn't be able to reach the beacon through its service name. There's a possibility the first command will fail if the cpos_test_network is not created by the time cpos_node or cpos_beacon is deployed. If this happens, run the command again. Unfortunately, we cannot guarantee the order of deploy with Docker Swarm.

If you want to monitor the logs to see what's going on, you can use these commands:

```
$ docker service logs --follow --raw cpos_node
$ docker service logs --follow --raw cpos_node_dishonest
$ docker service logs --follow --raw cpos_beacon
```

The first one refers to the node, and the second one to the beacon. You can press CTRL + C to exit the logs.


After all the data has been collected and the resulting .data files have been moved into the folder demo/logs you can process the data by running the command:

```
$ python demo/process_data.py
```

Finally, to remove the stack, run the following command:

```
$ docker stack rm cpos
```
