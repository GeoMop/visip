import sys
import time
import socket


file_name = sys.argv[1]
file_size = int(sys.argv[2])
with open(file_name, "wb") as fd:
    data = b"\0" * file_size
    fd.write(data)

time.sleep(10)

print(time.time())

print(socket.gethostname())
