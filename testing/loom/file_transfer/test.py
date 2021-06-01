from loom.client import Client, tasks

import os
import time

client = Client("localhost", 9010)   # Create a client object


def one_pass(file_size=10):
    gen_task = tasks.run(("python3", os.path.abspath("gen_task.py"), "file.bin", str(file_size)), outputs=(None, "file.bin"))
    gen_task.resource_request = tasks.cpus(1)

    rec_task = tasks.run(("python3", os.path.abspath("rec_task.py"), "file.bin"), [(tasks.get(gen_task, 1), "file.bin")])
    rec_task.resource_request = tasks.cpus(2)

    wait_task = tasks.run(("python3", os.path.abspath("wait_task.py"), "5"))
    wait_task.resource_request = tasks.cpus(2)

    results = client.submit((tasks.get(gen_task, 0), rec_task, wait_task))    # Submit tasks; returns list of futures
    res = client.gather(results)

    s = res[0].decode().split(maxsplit=2)
    t1 = float(s[0])
    host1 = s[1]

    s = res[1].decode().split(maxsplit=2)
    t2 = float(s[0])
    host2 = s[1]

    print("host1:", host1)
    print("host2:", host2)

    return t2 - t1


def multi_pass(file_size=10, pass_num=10):
    print("-------------------------------")
    print("File size:", file_size)

    t_list = []
    for i in range(pass_num):
        print("pass", i + 1)
        t = one_pass(file_size)
        t_list.append(t)
        print("t: {:.6f} s".format(t))
        time.sleep(5)

    print()
    print("Mean time: {:.6f} s".format(sum(t_list) / len(t_list)))
    print()


multi_pass(10)
multi_pass(1024 ** 2)
multi_pass(1024 ** 3)
