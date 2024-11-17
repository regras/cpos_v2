# CPoS v.2 - A refactored and improved implementation of Commiteeless Proof-of-Stake consensus algorithm

Blockchain technology offers a robust framework for decentralized data storage and processing. Among its various consensus algorithms, Committeeless Proof-of-Stake (CPoS) emerges as a promising alternative to the well-known Proof-of-Work and Proof-of-Stake mechanisms. CPoS distinguishes itself with lower power consumption and a simplified design that eliminates the need for validation committees.

Although still in its early stages, CPoS has shown promising results since its initial implementation and has undergone continuous enhancements. This updated version introduces new features that improve the algorithm’s readability, operability, and maintainability.

The repository's content is detailed in the article "Evaluating the Network Traffic on an Improved Version of the Committeeless Proof-of-Stake Blockchain Consensus Algorithm". This work was presented at the Workshop on Scientific Initiation and Undergraduate Works (WTICG), an event integrated with the Brazilian Symposium on Information and Computational Systems Security (SBSeg 2024). The article is accessible via DOI: 10.5753/sbseg_estendido.2024.243386.

# Abstract

This repository contains the source code used to generate the data presented in the aforementioned article. Additionally, the README.md file provides detailed instructions on running simulations and collecting the corresponding data.

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

As a basic test, you can run all network nodes locally on a single machine. The docker-compose-local.yml file includes environment variables that control various parameters for both the consensus mechanism and the network configuration. You can modify these variables as needed, ensuring that the value of TOTAL_STAKE matches the total number of nodes (replicas) in the network.

For the tests described in the article, the number of node_dishonest replicas was set to 0. The provided configuration file includes a default set of parameters for a demo run, which you can adjust to suit your needs. Below are examples of some customizable parameters available through Docker Compose's environment variables:
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

**Note:** It is important to note that each node in the network is configured to run for 30 rounds. However, the starting round number is not fixed at 0. Instead, it is calculated based on the number of round intervals elapsed since the reference timestamp: 2024-06-01 00:00:00. As a result, the execution will begin at a specific round number 𝑥, and proceed approximately until 𝑥+30. Due to potential variations in the nodes' internal clocks, there may be minor discrepancies in the exact starting round 𝑥 among the nodes. This lack of perfect synchronization is inherent to the system and applies universally across all methods of running the simulation.

## Running with distributed nodes

To run the system with distributed nodes, you need to set up a [Docker Swarm set up](https://docs.docker.com/engine/swarm/swarm-tutorial/) with a single Manager node. Ensure that the required ports are open on all nodes participating in the swarm to enable proper communication.

After setting up the Docker Swarm, you can configure the environment variables in the docker-compose.yml file. Key parameters, such as the variable Tau, the round time, and others, can be customized according to your needs. Ensure that the value of TOTAL_STAKE matches the total number of node replicas in the network.

For the tests described in the SBSeg article, the number of replicas for node_dishonest was set to 0. The provided file includes a default set of parameters optimized for a demo run, but you are free to modify them as needed.

To copy log files for processing and data extraction, complete the specified fields in the configuration to enable data transfer from the containers to a centralized machine. This setup ensures that logs are properly aggregated for further analysis.

1. `SSH_ADDRESS`: user@address of the machine you want to send the data to;
2. `SSH_PASSWORD`: the password for the account;
3. `SCP_PATH`: the full path where you want to send the data to.

Once everything is configured, you can start the system using the following commands:

```
$ docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node cpos_node_dishonest
$ docker stack deploy -c docker-compose.yml cpos
```

To ensure proper deployment, you must remove the cpos_node service and redeploy the stack. This is necessary because the cpos_node or cpos_node_dishonest services must start after the cpos_beacon service, and Docker Swarm does not guarantee deployment order. If the nodes start before the beacon, they will fail to resolve its service name.

There is a chance the initial command might fail if the cpos_test_network is not created before deploying cpos_node or cpos_beacon. If this occurs, simply rerun the command. Unfortunately, Docker Swarm does not provide a built-in way to enforce deployment order.

To ensure the beacon does not register any nodes from the first deployment attempt, wait for a period equivalent to six times the round time before executing the second command. This allows the beacon's list to empty and ensures proper registration.

If you want to monitor the logs to see what's going on, you can use these commands:

```
$ docker service logs --follow --raw cpos_node
$ docker service logs --follow --raw cpos_node_dishonest
$ docker service logs --follow --raw cpos_beacon
```

The first command corresponds to the node, while the second one is for the beacon. You can monitor the logs for both processes and press CTRL + C to exit the logs when done.

After collecting all the data and moving the resulting .data files into the demo/logs folder, you can process the data by running the following command inside a Poetry shell:

```
$ python demo/process_data.py
```

Finally, to remove the stack, run the following command:

```
$ docker stack rm cpos
```

## Running with distributed nodes automatically

In order to run the experiments automatically, you can use the provided bash script by executing it as follows:

```
$ ./demo/run_experiments.sh
```

With the configuration provided in the GitHub version of this script, it will automatically run the same experiments as those described in the SBSeg article. Make sure to properly configure the SSH_ADDRESS and SSH_PASSWORD in the docker-compose.yml file, so that the logs are copied to the desired location. Additionally, ensure that the value of TOTAL_STAKE matches the total number of node replicas in the network.

Next, you can configure the demo/process_data.py script’s log directory to process the data files from each experiment. Below is an example of how to set the log directory for processing:

```
log_dir = join(cwd, "demo/logs/5_5_1")
```

Next, you can configure the demo/process_data.py script’s log directory to process the data files from each experiment. Below is an example of how to set the log directory for processing:

```
$ python demo/process_data.py
```

# Examples of parameter customization for executions

You can modify various parameters used in the execution by editing the relevant files: docker-compose-local.yml, docker-compose.yml, or demo/run_experiments.sh, depending on the type of execution. Below are a few examples:

- Changing the "tau" parameter for CPoS:
  - For the local network, edit line 30 in docker-compose-local.yml.
  - For the non-automatic distributed network, modify line 53 in docker-compose.yml.
  - For the automatic distributed network, update line 22 in demo/run_experiments.sh.

- Adjusting the round duration:
  - For the local network, change lines 11 and 20 in docker-compose-local.yml.
  - For the non-automatic distributed network, adjust lines 20 and 51 in docker-compose.yml.
  - For the automatic distributed network, modify line 23 in demo/run_experiments.sh.

- Changing the number of nodes in the CPoS network:
  - Ensure that the TOTAL_STAKE value matches the number of nodes.
  - For the local network, modify lines 21 and 31 in docker-compose-local.yml.
  - For both automatic and non-automatic distributed networks, adjust lines 25 and 54 in docker-compose.yml.

These modifications allow you to customize various aspects of the network and experiment setup.
