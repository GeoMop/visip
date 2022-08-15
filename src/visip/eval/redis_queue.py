from visip.dev.data import serialize, deserialize

import redis
import queue


class RedisQueue:
    def __init__(self, id=-1, host='localhost', port=6379):
        self.client = redis.Redis(host=host, port=port, db=1)

        if id < 0:
            id = self.client.incrby("queue_last_id")
        self.id = id

    def put(self, value):
        bin_data = serialize(value)
        self.client.rpush(str(self.id), bin_data)

    def get(self, timeout=None):
        if timeout is None:
            bin_data = self.client.blpop([str(self.id)])[1]
        elif timeout > 0:
            bin_data = self.client.blpop([str(self.id)], timeout=timeout)
            if bin_data is not None:
                bin_data = bin_data[1]
        else:
            bin_data = self.client.lpop(str(self.id))

        if bin_data is not None:
            value = deserialize(bin_data)
            return value
        else:
            raise queue.Empty

    def get_nowait(self):
        return self.get(timeout=0.0)

    def clear(self):
        self.client.ltrim(str(self.id), 1, 0)
