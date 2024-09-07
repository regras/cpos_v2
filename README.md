# WTICG SBSeg24 Article

This repository is tied to the article "Evaluating the network traffic on an improved version of the Committeeless Proof-of-Stake blockchain consensus algorithm" published in the Workshop on Scientific Initiation and Undergraduate Works (WTICG), an event integrated with the Brazilian Symposium on Information and Computational Systems Security (SBSeg).

Article's abstract: Blockchain is a powerful way to store and process data in a decentralized manner. Among its consensus algorithms, Committeeless Proof-of-Stake (CPoS) comes as a promising alternative to the better-known Proof-of-Work and Proof-of-Stake, with its reduced power consumption and more straightforward design without validation committees. However, CPoS is still an emerging algorithm and requires extensive testing to validate its correctness and efficiency. Its first implementation was promising and showed satisfactory results, but it has been enhanced continuously. This article aims to present the new characteristics added to CPoS and evaluate their impact on the data traffic and on the scheme as a whole.

# Abstract

This repository stores the source code used for collecting the data for the aforementioned article. The file README.md also gives instructions on how to run the simulations and collect the data.

# Running the simulation

## Dependencies

- Docker 24.0
- Python 3.11
- Docker Compose 2.20
- Poetry 1.6.1

We recommend running the process_data.py script on Linux Ubuntu 20.04.

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

As a minimum test, you can run all the network's nodes in a local machine. The file docker-compose-local.yml contains environment variables that control various parameters for the consensus mechanism and the network. These values can be changed, just make sure that the value of TOTAL_STAKE corresponds to the total number of nodes in the network (replicas). For this article, the number of replicas of node_dishonest was kept at 0. The version of the file available already contains a default set of parameters for a demo run, but you can change it accordingly if you desire. Below is an example of some parameters you can customize through Docker Compose's environment variables:

```
environment:
      - BEACON_IP=beacon
      - BEACON_PORT=9000
      - PORT=8888
      - ROUND_TIME=20
      - TOLERANCE=2
      - TAU=3
      - TOTAL_STAKE=5
```

You can launch a local network with the command:

```
$ docker compose --file docker-compose-local.yml up
```

It will stop running when it gets to round 30. To process the generated data, run (make sure to do it within a Poetry shell environment):

```
$ python demo/process_data.py
```

After the simulation is done, be sure to run the following command to take down the docker nodes (specially before running another simulation).

```
$ docker compose --file docker-compose-local.yml down
```

The execution of the program beeing halted does not take down the docker node, therefore it is necessary to run the command presented above after all the nodes have halted.

**Note:** It is importante to note that each node in the network is programmed to run for 30 rounds. However, the round number does not start at 0. It is determined by the number of round times since the date and time 2024-06-01 00:00:00. So the execution will start in a round number x, and run until approximatelly x + 30. The nodes can have small disagreements amongst themselves in what round "x" the execution started, since their internal clocks might not be perfectly synchronized. This applies to all the ways of running the simulation.

## Running with distributed nodes

To run with distributed nodes, you should have a [Docker Swarm set up](https://docs.docker.com/engine/swarm/swarm-tutorial/) with only one Manager. Be sure to have the specified ports open on every node.

After that, you can configure the environment variables on `docker-compose.yml`, such as the variable Tau, the round time, etc.. Just make sure that the value of TOTAL_STAKE corresponds to the total number of node replicas in the network. For this article, the number of replicas of node_dishonest was kept at 0. The version of the file available already contains a default set of parameters for a demo run, but you can change it accordingly if you desire.

If you want to copy the log files to process and extract some data, fill the following fields accordingly, so that the data will be sent from the containers to a centralized machine:

1. `SSH_ADDRESS`: user@address of the machine you want to send the data to;
2. `SSH_PASSWORD`: the password for the account;
3. `SCP_PATH`: the full path where you want to send the data to.

Now, with everything configured, you can start the scheme with the following commands:

```
$ docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node cpos_node_dishonest
$ docker stack deploy -c docker-compose.yml cpos
```

You have to remove the cpos_node service and then deploy the stack again because the cpos_node / cpos_node_dishonest has to deploy after the cpos_beacon, and there isn't a way to guarantee the deploy order with Docker Swarm. Otherwise, the nodes wouldn't be able to reach the beacon through its service name. There's a possibility the first command will fail if the cpos_test_network is not created by the time cpos_node or cpos_beacon is deployed. If this happens, run the command again. Unfortunately, we cannot guarantee the order of deploy with Docker Swarm. To make sure the beacon doesn't register any of the nodes from the first deploy, wait at least 6 times the round time before running the second command, so that it empties its list.

If you want to monitor the logs to see what's going on, you can use these commands:

```
$ docker service logs --follow --raw cpos_node
$ docker service logs --follow --raw cpos_node_dishonest
$ docker service logs --follow --raw cpos_beacon
```

The first and second ones refers to the nodes, and the third one to the beacon. You can press CTRL + C to exit the logs.

After all the data has been collected and the resulting .data files have been moved into the folder demo/logs you can process the data by running this command inside a poetry shell:

```
$ python demo/process_data.py
```

Finally, to remove the stack, run the following command:

```
$ docker stack rm cpos
```

## Running with distributed nodes automatically

In order to run the experiments automatically, you can use the bash script as follows:

```
$ ./demo/run_experiments.sh
```

With the configuration present on the Github version of this script, it will run the same experiments as the ones for the article. Be sure to configure the `SSH_ADDRESS` and `SSH_PASSWORD` (on the docker-compose.yml file) adequately so that the logs are copied somewhere. It is also important that the value of TOTAL_STAKE corresponds to the total number of node replicas in the network.

After that, you can configure the `demo/process_data.py` script's log directory to process each experiment's data files. Here's an example:

```
log_dir = join(cwd, "demo/logs/5_5_1")
```

Then, inside a poetry shell, you can process the data with the following command:

```
$ python demo/process_data.py
```

# Examples of changing parameters for the executions

It is possible to change some of the parameters used in the execution by modifying the files docker-compose-local.yml, docker-compose.yml or demo/run_experiments.sh depending on the type of execution. A few examples are:

- To change the values for the CPoS parameter “tau” used in the experiments, change line 30 of docker-compose-local.yml (for the local network); line 53 of docker-compose.yml (for the non-automatic distributed network); or line 22 of demo/run_experiments.sh (for the automatic distributed network).
- To change the values for the duration of a round used in the experiments, change lines 11 and 20 of docker-compose-local.yml (for the local network); lines 20 and 51 of docker-compose.yml (for the non-automatic distributed network); or line 23 of demo/run_experiments.sh (for the automatic distributed network).
- To change the number of nodes in the CPoS network, it is also necessary to guarantee that the total stake will be equal to the number of nodes. In order to change these parameters, modify the lines 21 and 31 of docker-compose-local.yml (for the local network); or lines 25 and 54 of docker-compose.yml (for both the automatic and non-automatic distributed networks)
