import subprocess
import tempfile
from pathlib import Path


class Transport:

    def run_shell(self, cmd: str, cwd: str = None, timeout: int = 120,
                  stdin_data: str = None) -> dict:
        raise NotImplementedError

    def close(self):
        pass


class LocalTransport(Transport):

    def run_shell(self, cmd: str, cwd: str = None, timeout: int = 120,
                  stdin_data: str = None) -> dict:
        r = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True,
            timeout=timeout, input=stdin_data,
        )
        return {"exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}


class SSHTransport(Transport):

    def __init__(self, host: str, user: str = None, port: int = 22,
                 key_path: str = None):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = str(Path(key_path).expanduser()) if key_path else None
        self._control_path = None

    def _ensure_control(self):
        if self._control_path is not None:
            return
        self._control_path = tempfile.mktemp(prefix="zsiga_ssh_")
        args = self._base_args() + [
            "-o", "ControlMaster=auto",
            "-o", f"ControlPath={self._control_path}",
            "-o", "ControlPersist=600",
            self._target(), "true",
        ]
        subprocess.run(args, capture_output=True, text=True, timeout=15)

    def _base_args(self) -> list[str]:
        args = ["ssh", "-o", "StrictHostKeyChecking=no",
                "-o", f"ControlPath={self._control_path or ''}"]
        if self.port != 22:
            args.extend(["-p", str(self.port)])
        if self.key_path:
            args.extend(["-i", self.key_path])
        return args

    def _target(self) -> str:
        return f"{self.user}@{self.host}" if self.user else self.host

    def run_shell(self, cmd: str, cwd: str = None, timeout: int = 120,
                  stdin_data: str = None) -> dict:
        self._ensure_control()
        full_cmd = f"cd '{cwd}' && {cmd}" if cwd else cmd
        args = self._base_args() + [self._target(), full_cmd]
        try:
            r = subprocess.run(
                args, capture_output=True, text=True,
                timeout=timeout, input=stdin_data,
            )
            return {"exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired:
            return {"exit_code": -1, "stdout": "", "stderr": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}

    def close(self):
        if not self._control_path:
            return
        args = ["ssh", "-o", f"ControlPath={self._control_path}",
                "-O", "exit", self._target()]
        subprocess.run(args, capture_output=True, text=True, timeout=5)
        self._control_path = None


def create_transport(target_config) -> Transport:
    ssh = getattr(target_config, "ssh", None)
    if not ssh:
        return LocalTransport()
    return SSHTransport(
        host=ssh.host,
        user=ssh.user,
        port=ssh.port,
        key_path=ssh.key_path,
    )
