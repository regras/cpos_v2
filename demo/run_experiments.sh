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
TAU_VALUES=(3 5 7 10)
ROUND_TIME_VALUES=(5 10 15 20)

# Loop over each TAU value
for TAU in "${TAU_VALUES[@]}"; do
    # Loop over each ROUND_TIME value
    for ROUND_TIME in "${ROUND_TIME_VALUES[@]}"; do
        # Run 10 times for each combination
        for i in {1..10}; do
            echo "Running Docker Compose with TAU=$TAU, ROUND_TIME=$ROUND_TIME (Run $i)"
            export TAU=$TAU
            export ROUND_TIME=$ROUND_TIME
            export SCP_PATH="~/logs/${TAU}_${ROUND_TIME}_${i}"

            # Bring up services in detached mode
            docker stack deploy -c docker-compose.yml cpos && docker service rm cpos_node
            sleep_duration=$((ROUND_TIME * 7))
            sleep $sleep_duration
            docker stack deploy -c docker-compose.yml cpos

            # Wait for all containers to exit
            echo "Waiting for containers to finish..."
             # Calculate and wait for the specified time
            sleep_time=$(calculate_sleep_time "$round_time")
            sleep "$sleep_time"

            # After all containers have finished, bring down services
            docker stack rm cpos
            sleep 30
        done
    done
done

echo "All runs completed."
