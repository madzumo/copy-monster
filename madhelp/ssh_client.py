import paramiko
import os


class SSHClient:
    """Run commands on remote Linux server interactively.
    Initiate with host, username & key file path."""

    def __init__(self, hostname, username, keyfile):
        self.hostname = hostname
        self.username = username
        self.shell_command = ''
        self.ssh_key_file = keyfile
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.command_output = ''

    def _connect_open(self):
        try:
            self.client.connect(self.hostname, username=self.username, key_filename=self.ssh_key_file)
            # print("SSH connection established")
            return True
        except Exception as ex:
            print({ex})
            return False

    def _connect_close(self):
        self.client.close()

    def _execute_command(self, show_output=True):
        try:
            stdin, stdout, stderr = self.client.exec_command(self.shell_command)
            self.command_output = stdout.read().decode()
            if show_output:
                print(self.command_output)
            # print(stderr.read().decode())
        except Exception as ex:
            print(f"An error occurred: {ex}")

    def run_command(self, execute_command, show_output=True):
        """Include the command you want to run via SSH"""
        self.shell_command = execute_command
        if self._connect_open():
            self._execute_command(show_output)
            self._connect_close()

    def ensure_remote_dir(self, sftp, remote_directory):
        """Ensure that the remote directory exists, create it if necessary."""
        # Split the path to get all directories and subdirectories
        dirs = remote_directory.split('/')
        current_dir = ''
        for dir_x in dirs:
            if dir_x:  # This skips empty strings to avoid issues with leading '/'
                current_dir += '/' + dir_x  # Construct the path with UNIX-like separators
                try:
                    sftp.stat(current_dir)
                except FileNotFoundError:
                    sftp.mkdir(current_dir)
                    print(f"Created remote directory: {current_dir}")

    def copy_contents(self, local_path, remote_path):
        """
        Copy a file or all contents of a folder. IF it's file you must name the file from and to destination.
        Same with folder.
        """
        if self._connect_open():
            scp = paramiko.SFTPClient.from_transport(self.client.get_transport())
            try:
                if os.path.isdir(local_path):
                    for item in os.listdir(local_path):
                        local_item_path = os.path.join(local_path, item)
                        remote_item_path = os.path.join(remote_path, item).replace('\\',
                                                                                   '/')
                        if os.path.isfile(local_item_path):
                            # Ensure the remote directory exists before copying
                            self.ensure_remote_dir(scp, os.path.dirname(remote_item_path))
                            scp.put(local_item_path, remote_item_path)
                            print(f"Copied file: {local_item_path} to {remote_item_path}")
                elif os.path.isfile(local_path):
                    # Ensure the remote directory exists before copying
                    self.ensure_remote_dir(scp, os.path.dirname(remote_path))
                    scp.put(local_path, remote_path)
                    print(f"Copied file: {local_path} to {remote_path}")
                else:
                    print("The specified local_path does not exist or is not accessible.")
            except Exception as e:
                print(f"Error copying contents:{e}\n{local_path}\n{remote_path}")
            finally:
                scp.close()
                self.client.close()
        else:
            print("Failed to open connection.")
