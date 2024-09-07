#!/bin/bash

calculate_sleep_time() {
    local round_time=$1
    local base_sleep=120
    local additional_sleep=$(( round_time * 30 ))
    echo $(( base_sleep + additional_sleep ))
}

# Function to check if all containers have exited
check_containers_exited() {
    local exited_containers
    exited_containers=$(docker compose --file docker-compose-local.yml ps -q | xargs docker inspect -f '{{.State.Status}}' | grep -v 'exited' | wc -l)
    if [ "$exited_containers" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Define arrays for TAU and ROUND_TIME values
TAU=3
ROUND_TIME=10
NUM_PEERS=(3 5 10)
NODE_DISHONEST_REPLICA_VALUES=(3 5 8 10 13 15)


DISHONEST_BROADCAST_CREATED_BLOCK="true"
DISHONEST_BROADCAST_RECEIVED_BLOCK="false"
# Run 3 times for each combination
for i in {6..7}; do
    for NUM_PEER in "${NUM_PEERS[@]}"; do
        for NODE_DISHONEST_REPLICAS in "${NODE_DISHONEST_REPLICA_VALUES[@]}"; do
            echo "Running Docker Compose with TAU=$TAU, NODE_DISHONEST_REPLICAS=$NODE_DISHONEST_REPLICAS, NUM_PEERS=$NUM_PEER (Run $i)"
            export TAU=$TAU
            export ROUND_TIME=$ROUND_TIME
            export NUM_PEER=$NUM_PEER
            export MINIMUM_NUM_PEERS=$((NUM_PEER - 1))
            export MAXIMUM_NUM_PEERS=$((NUM_PEER + 2))
            export NODE_REPLICAS=$((25 - NODE_DISHONEST_REPLICAS))
            export NODE_DISHONEST_REPLICAS=$NODE_DISHONEST_REPLICAS
            export DISHONEST_BROADCAST_CREATED_BLOCK=$DISHONEST_BROADCAST_CREATED_BLOCK
            export DISHONEST_BROADCAST_RECEIVED_BLOCK=$DISHONEST_BROADCAST_RECEIVED_BLOCK
            export SCP_PATH="~/logs/${NUM_PEER}peers/${NODE_DISHONEST_REPLICAS}_${DISHONEST_BROADCAST_CREATED_BLOCK}_${DISHONEST_BROADCAST_RECEIVED_BLOCK}_${i}"

            # Bring up services in detached mode
            docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node cpos_node_dishonest
            sleep_duration=$((ROUND_TIME * 7))
            sleep $sleep_duration
            docker stack deploy -c docker-compose.yml cpos

            # Wait for all containers to exit
            echo "Waiting for containers to finish..."
            # Calculate and wait for the specified time
            sleep_time=$(calculate_sleep_time "$ROUND_TIME") # CHANGE THIS TO APPROPRIATE NUMBER OF ROUNDS BEFORE EXECUTION
            sleep "$sleep_time"

            # After all containers have finished, bring down services
            docker stack rm cpos
            sleep 30
        done
    done
done

DISHONEST_BROADCAST_CREATED_BLOCK="false"
DISHONEST_BROADCAST_RECEIVED_BLOCK="true"
# Run 3 times for each combination
for i in {6..7}; do
    for NUM_PEER in "${NUM_PEERS[@]}"; do
        for NODE_DISHONEST_REPLICAS in "${NODE_DISHONEST_REPLICA_VALUES[@]}"; do
            echo "Running Docker Compose with TAU=$TAU, NODE_DISHONEST_REPLICAS=$NODE_DISHONEST_REPLICAS, NUM_PEERS=$NUM_PEER (Run $i)"
            export TAU=$TAU
            export ROUND_TIME=$ROUND_TIME
            export NUM_PEER=$NUM_PEER
            export MINIMUM_NUM_PEERS=$((NUM_PEER - 1))
            export MAXIMUM_NUM_PEERS=$((NUM_PEER + 2))
            export NODE_REPLICAS=$((25 - NODE_DISHONEST_REPLICAS))
            export NODE_DISHONEST_REPLICAS=$NODE_DISHONEST_REPLICAS
            export DISHONEST_BROADCAST_CREATED_BLOCK=$DISHONEST_BROADCAST_CREATED_BLOCK
            export DISHONEST_BROADCAST_RECEIVED_BLOCK=$DISHONEST_BROADCAST_RECEIVED_BLOCK
            export SCP_PATH="~/logs/${NUM_PEER}peers/${NODE_DISHONEST_REPLICAS}_${DISHONEST_BROADCAST_CREATED_BLOCK}_${DISHONEST_BROADCAST_RECEIVED_BLOCK}_${i}"

            # Bring up services in detached mode
            docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node cpos_node_dishonest
            sleep_duration=$((ROUND_TIME * 7))
            sleep $sleep_duration
            docker stack deploy -c docker-compose.yml cpos

            # Wait for all containers to exit
            echo "Waiting for containers to finish..."
            # Calculate and wait for the specified time
            sleep_time=$(calculate_sleep_time "$ROUND_TIME") # CHANGE THIS TO APPROPRIATE NUMBER OF ROUNDS BEFORE EXECUTION
            sleep "$sleep_time"

            # After all containers have finished, bring down services
            docker stack rm cpos
            sleep 30
        done
    done
done

DISHONEST_BROADCAST_CREATED_BLOCK="false"
DISHONEST_BROADCAST_RECEIVED_BLOCK="false"
# Run 3 times for each combination
for i in {6..7}; do
    for NUM_PEER in "${NUM_PEERS[@]}"; do
        for NODE_DISHONEST_REPLICAS in "${NODE_DISHONEST_REPLICA_VALUES[@]}"; do
            echo "Running Docker Compose with TAU=$TAU, NODE_DISHONEST_REPLICAS=$NODE_DISHONEST_REPLICAS, NUM_PEERS=$NUM_PEER (Run $i)"
            export TAU=$TAU
            export ROUND_TIME=$ROUND_TIME
            export NUM_PEER=$NUM_PEER
            export MINIMUM_NUM_PEERS=$((NUM_PEER - 1))
            export MAXIMUM_NUM_PEERS=$((NUM_PEER + 2))
            export NODE_REPLICAS=$((25 - NODE_DISHONEST_REPLICAS))
            export NODE_DISHONEST_REPLICAS=$NODE_DISHONEST_REPLICAS
            export DISHONEST_BROADCAST_CREATED_BLOCK=$DISHONEST_BROADCAST_CREATED_BLOCK
            export DISHONEST_BROADCAST_RECEIVED_BLOCK=$DISHONEST_BROADCAST_RECEIVED_BLOCK
            export SCP_PATH="~/logs/${NUM_PEER}peers/${NODE_DISHONEST_REPLICAS}_${DISHONEST_BROADCAST_CREATED_BLOCK}_${DISHONEST_BROADCAST_RECEIVED_BLOCK}_${i}"

            # Bring up services in detached mode
            docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node cpos_node_dishonest
            sleep_duration=$((ROUND_TIME * 7))
            sleep $sleep_duration
            docker stack deploy -c docker-compose.yml cpos

            # Wait for all containers to exit
            echo "Waiting for containers to finish..."
            # Calculate and wait for the specified time
            sleep_time=$(calculate_sleep_time "$ROUND_TIME") # CHANGE THIS TO APPROPRIATE NUMBER OF ROUNDS BEFORE EXECUTION
            sleep "$sleep_time"

            # After all containers have finished, bring down services
            docker stack rm cpos
            sleep 30
        done
    done
done

echo "All runs completed."
