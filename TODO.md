- Fix the node tests
- Refactor the logging subsystem
    - Lots of repeated code (for basically every class that uses logging)
    - Unable to log to a file
- Maybe implement some sort of heartbeat between the beacon and the nodes
    - Or drop peers from the local node peerlist after too many "host unreachable" errors
- Make data dumping better/more configurable while we don't implement database communication
- Write better tests with some kind of mock infrastructure (especially for core/blockchain) so that we can test the general behavior of the module without having to hard-code specific examples
    - Currently the `[core/blockchain]` tests are failing because of hard-coded pubkeys no longer passing tests after some implementation logic changes
- Debug and write proper tests for fork detection
