echo "starting container..."

# Database related commands
service mariadb start
echo "initializing mempool"
mysql -e "CREATE USER 'CPoS'@localhost IDENTIFIED BY 'CPoSPW';"
mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'CPoS'@'localhost';"
mysql -e "CREATE DATABASE mempool;"
mysql mempool < cpos/db/mempool.sql
echo "initializing local blockchain database"
mysql -e "CREATE DATABASE localBlockchain;"
mysql localBlockchain < cpos/db/localBlockchain.sql

# CPoS related commands
export GENESIS_TIMESTAMP=$(date +%s)
echo "GENESIS_TIMESTAMP: $GENESIS_TIMESTAMP"
poetry run python demo/main.py --beacon-ip $BEACON_IP --beacon-port $BEACON_PORT -p $PORT --genesis-timestamp $GENESIS_TIMESTAMP --total-rounds 30 &
pid=$!
trap "kill -SIGTERM $pid" INT TERM
wait $pid
echo "exiting!"
