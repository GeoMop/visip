"""
Functions for uniform manipulation of the data. These functions treat the basic types and all attr classes.
We SHOULD support:
- representation
- serialization into a bytearray
- deserialization from a byte array
- hash

TODO:
- use renamed jsondata lib for serialization and deserialization of the VISIP data
- need support for numpy objects
- use serialized object for hashing instead of its str repr.
- use some serious hashing function

Same special dataclasses are implemented, in particular:
- file wrapper
- ...
"""
from typing import NewType
import pickle
import hashlib

from .dtype import DataClassBase

HashValue = NewType('HashValue', bytes)

default_hash = hashlib.sha256
def my_hash(x, seed=b""):
    m = default_hash()
    m.update(x)
    m.update(seed)
    return m.digest()

hasher_fn = my_hash
def hash_stream(stream: bytearray, previous:HashValue=b"") -> HashValue:
    """
    Compute the hash of the bytearray.
    We use fast non-cryptographic hashes long enough to keep probability of collision rate at
    1 per age of universe for the expected world's computation power in year 2100.

    Serves as an interface to a hash function used in whole analysis evaluation:
    - task IDs
    - input and result hashes
    - ResultsDB
    """
    return hasher_fn(stream, seed=previous)

def hash(data, previous=b""):
    #return hash_stream(str(data).encode('utf-8'), previous)
    if isinstance(data, int):
        int_data = int(data)
        return hash_stream(int_data.to_bytes(8,'big',signed=True))

    hash_method = None
    try:
        hash_method = data.__hash__
    except AttributeError:
        pass
    if hash_method is not None:
        return hash_stream(hash_method().to_bytes(8, 'big', signed=True), previous)
    else:
        return hash_stream(str(data).encode('utf-8'), previous)

def hash_file(file_path):
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    m = default_hash()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            m.update(data)
    return m.digest()


def serialize(data):
    """
    Serialize a data tree 'data' into a byte array.
    :param data:
    :return:
    """
    def inner(data):
        # if data type is Class
        if isinstance(data, DataClassBase):
            new_data_dict = {name: inner(d) for name, d in data.__dict__.items()}
            data = ("__class__", data.__class__.__module__, data.__class__.__name__, new_data_dict)

        elif isinstance(data, list):
            data = [inner(d) for d in data]

        elif isinstance(data, tuple):
            data = tuple(inner(d) for d in data)

        elif isinstance(data, dict):
            data = {name: inner(d) for name, d in data.items()}

        return data

    return pickle.dumps(inner(data))


def deserialize(stream: bytearray):
    """
    Deserialize a data tree.
    :param stream:
    :return:
    """
    data = pickle.loads(stream)

    from visip.dev.module import Module

    def inner(data):
        # if data type is Class
        if isinstance(data, tuple) and data[0] == "__class__":
            action = Module.resolve_function(data[1], data[2])
            new_data_dict = {name: inner(d) for name, d in data[3].items()}
            obj = action._data_class.__new__(action._data_class)
            obj.__dict__ = new_data_dict
            data = obj

        elif isinstance(data, list):
            data = [inner(d) for d in data]

        elif isinstance(data, tuple):
            data = tuple(inner(d) for d in data)

        elif isinstance(data, dict):
            data = {name: inner(d) for name, d in data.items()}

        return data

    return inner(data)
