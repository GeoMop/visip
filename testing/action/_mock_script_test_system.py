import sys
# call: ['python', script, "-m", self.msg_file, 123]

assert sys.argv[1] == "-m"
with open(sys.argv[2]) as f:
    content = f.read()
    assert content == "Hallo world\n"
assert sys.argv[3] == "123"
print("I'm here.")
