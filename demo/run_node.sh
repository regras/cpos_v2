echo "starting container..."
export GENESIS_TIMESTAMP=$(date +%s)
echo "GENESIS_TIMESTAMP: $GENESIS_TIMESTAMP"
poetry run python demo/main.py --beacon-ip $BEACON_IP --beacon-port $BEACON_PORT -p $PORT --genesis-timestamp $GENESIS_TIMESTAMP --total-rounds 30 &
pid=$!
trap "kill -SIGTERM $pid" INT TERM
wait $pid
echo "exiting!"
