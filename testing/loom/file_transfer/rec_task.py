import sys
import time
import socket


print(time.time())

file_name = sys.argv[1]
with open(file_name, "rb") as fd:
    data = fd.read()

print(socket.gethostname())
