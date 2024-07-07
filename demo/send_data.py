from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

import os

def createSSHClient(hostname, user, password, port=22):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(hostname, port, user, password, banner_timeout=200)
    return client

def create_remote_directory(ssh, remote_directory):
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_directory}")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print(f"Successfully created or verified directory: {remote_directory}")
    else:
        print(f"Error creating directory: {stderr.read().decode()}")

ssh_address = os.environ.get("SSH_ADDRESS", "")
ssh_password = os.environ.get("SSH_PASSWORD", "")
scp_filepath = os.environ.get("SCP_PATH", "")
local_filepath = "./demo/logs/"
max_retries = 5

def send_data():

    if ssh_address and ssh_password and scp_filepath:
        for retry in range(max_retries):
            try:
                print(f"Sending log files to {ssh_address} at {scp_filepath}")

                ssh_user, ssh_hostname = ssh_address.split("@")
                ssh = createSSHClient(ssh_hostname, ssh_user, ssh_password)

                # Create remote directory if it doesn't exist
                create_remote_directory(ssh, scp_filepath)

                scp = SCPClient(ssh.get_transport())
                scp.put(files=local_filepath, remote_path=scp_filepath, recursive=True)

                print("Finished copying log files!")
                break
            except:
                if retry < max_retries - 1:
                    print("Trying to send SCP again!")
                else:
                    print("Failed to send data through SCP")

    else:
        print("Couldn't send data! SSH address and/or password and/or scp path not specified.")

if __name__ == "__main__":
    send_data()