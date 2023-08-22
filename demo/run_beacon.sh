poetry run python ./demo/beacon.py -p $PORT &
pid=$!
trap "kill -SIGTERM $pid" INT TERM
wait $pid
