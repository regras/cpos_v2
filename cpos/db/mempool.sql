CREATE TABLE IF NOT EXISTS transactions (
        transaction_id VARCHAR(256) NOT NULL,
        value integer,
        input_address text NOT NULL,
        output_address text NOT NULL,
        committed integer default 0,
        choosen integer default 0,
        transaction_hash text NOT NULL,
        data text NOT NULL,
        timestamp text NOT NULL,
        PRIMARY KEY (transaction_id))
