echo "starting container"
poetry run python demo/main.py --beacon-ip $BEACON_IP --beacon-port $BEACON_PORT -p $PORT --genesis-timestamp $GENESIS_TIMESTAMP &
pid=$!
trap "kill -SIGTERM $pid" INT TERM
wait $pid
echo "exiting!"
