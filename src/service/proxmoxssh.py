from paramiko.channel import ChannelFile, ChannelStderrFile
from paramiko import SSHClient, SSHException
from configuration import infolog, warnlog
import json


class ProxmoxSSHClient():
    def __init__(self, host: str, user: str, password: str):
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.connect(hostname=host,
                            username=user,
                            password=password)

    def __del__(self):
        self.client.close()

    def execute(self, cmd: str) -> str:
        sstdin, stdout, stderr = self.client.exec_command(cmd)
        self._handle_stderr(stderr)
        return self._handle_stdout(stdout)

    def get(self, api_path: str) -> dict | list:
        return self._request(api_path, "get")

    def post(self, api_path: str) -> dict | list:
        return self._request(api_path, "create")

    def put(self, api_path: str) -> dict | list:
        return self._request(api_path, "set")

    def delete(self, api_path: str) -> dict | list:
        return self._request(api_path, "delete")

    def _request(self, api_path: str, method: str) -> dict | list | str:
        sstdin, stdout, stderr = self.client.exec_command(
            f"pvesh {method} {api_path} --output-format json")
        self._handle_stderr(stderr)
        return self._handle_stdout(stdout)

    def _handle_stderr(self, stderr: ChannelStderrFile):
        stderr: str = stderr.read().decode('utf-8')
        if "WARNING" in stderr:
            self._handle_output(stderr)
        elif stderr:
            raise SSHException(stderr)

    def _handle_stdout(self, stdout: ChannelFile):
        stdout: str = stdout.read().decode("utf-8")
        try:
            return json.loads(stdout)
        except:
            self._handle_output(stdout)
            return stdout

    def _handle_output(self, output: str):
        output = output.strip('\n').split('\n')
        for message in output:
            if "WARNING" in message:
                warnlog.warning(message.strip("WARNING: ").strip(' '))
            elif message:
                infolog.info(message.strip(' '))
