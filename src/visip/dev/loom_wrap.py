import os
import sys
import subprocess


args = sys.argv[1:]
if not args:
    sys.exit(1)

print("wrapper")
print(args)

process = subprocess.Popen(args)
process.wait()

out_name = "output_files"
if os.path.isfile(out_name):
    with open(out_name) as fd:
        output_files = [line.rstrip() for line in fd]
    for f in output_files:
        if not os.path.isfile(f):
            dir = os.path.dirname(f)
            os.makedirs(dir, exist_ok=True)
            open(f, 'a').close()
