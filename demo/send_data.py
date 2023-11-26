from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

import os

def createSSHClient(hostname, user, password, port=22):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(hostname, port, user, password)
    return client

ssh_address = os.environ.get("SSH_ADDRESS", "")
ssh_password = os.environ.get("SSH_PASSWORD", "")
scp_filepath = os.environ.get("SCP_PATH", "")
local_filepath = "./demo/logs"

if ssh_address and ssh_password and scp_filepath:
    ssh_user, ssh_hostname = ssh_address.split("@")
    ssh = createSSHClient(ssh_hostname, ssh_user, ssh_password)
    scp = SCPClient(ssh.get_transport())
    scp.put(files=local_filepath, remote_path=scp_filepath, recursive=True)

    print("Finished copying log files!")

else:
    print("Couldn't send data! SSH address and/or password and/or scp path not specified.")
