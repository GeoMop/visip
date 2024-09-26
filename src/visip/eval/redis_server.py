import os
import subprocess


class RedisServer:
    """
    Class for running Redis db.
    It assumes that Redis is installed with binary at /usr/bin/redis-server.
    """
    def __init__(self, data_dir="", port=6379):
        self.data_dir = os.path.abspath(data_dir)
        self.port = port
        self.proc = None

    def start(self):
        """
        Starts the db.
        :return:
        """
        if self.proc is not None:
            return

        os.makedirs(self.data_dir, exist_ok=True)
        args = ["/usr/bin/redis-server", "--protected-mode", "no", "--port", str(self.port), "--save", "300", "1"]
        # WARNING: "protected-mode no" means that db is open to all interfaces with no security
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=self.data_dir)

    def stop(self):
        """
        Stops the db.
        :return:
        """
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None
