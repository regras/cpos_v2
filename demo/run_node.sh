echo "starting container"
GENESIS_TIMESTAMP=$(python -c "import time; print(int(time.time()))")
poetry run python demo/main.py --beacon-ip $BEACON_IP --beacon-port $BEACON_PORT -p $PORT --genesis-timestamp $GENESIS_TIMESTAMP --total-rounds 30 &
pid=$!
trap "kill -SIGTERM $pid" INT TERM
wait $pid
echo "exiting!"
