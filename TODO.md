- Fix the node tests
- Refactor the logging subsystem
    - Lots of repeated code (for basically every class that uses logging)
    - Unable to log to a file
- Implement resync between nodes
- Maybe implement some sort of heartbeat between the beacon and the nodes
    - Or drop peers from the local node peerlist after too many "host unreachable" errors
- Use list[Peer] in cpos.p2p.network? Or at least find a way to pretty-print the peer IDs
- We need to reevaluate the block confirmation/fork detection algorithm for the case where nodes have uneven stakes (and are potentially able to generate several blocks, but will only broadcast one)
- Investigate race condition in confirmation mechanism where nodes take some time to synchronize between each other,
  messing up the average successful sortition statistics and making it impossible to confirm blocks
- Make data dumping better/more configurable while we don't implement database communication
- Write better tests with some kind of mock infrastructure (especially for core/blockchain) so that we can test
  the general behavior of the module without having to hard-code specific examples
