import redis
import time
import sys


client = redis.Redis(host='localhost', port=6379, db=0)

data_size = 100 * 1024**2
count = 10

data = b"\0" * data_size


def get_wait(data_id):
    value = None
    while not value:
        value = client.get(str(data_id))


def node_1():
    client.flushdb()
    time.sleep(5)

    t = time.time()

    for i in range(count):
        client.set(str(i), data)
        get_wait(count + i)

    dt = time.time() - t
    print("total: {:.6f} s".format(dt))
    print("one: {:.6f} s".format(dt / count))

    client.flushdb()


def node_2():
    client.flushdb()

    for i in range(count):
        get_wait(i)
        client.set(str(count + i), data)


def node_one():
    client.flushdb()
    time.sleep(5)

    t = time.time()

    for i in range(count):
        client.set(str(i), data)
        get_wait(i)

        client.set(str(count + i), data)
        get_wait(count + i)

    dt = time.time() - t
    print("total: {:.6f} s".format(dt))
    print("one: {:.6f} s".format(dt / count))

    client.flushdb()


if __name__ == "__main__":
    node_id = sys.argv[1]
    if node_id == "1":
        node_1()
    elif node_id == "2":
        node_2()
    elif node_id == "one":
        node_one()
