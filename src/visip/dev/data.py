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

    return pickle.dumps(data)


def deserialize(stream: bytearray):
    """
    Deserialize a data tree.
    :param stream:
    :return:
    """
    return pickle.loads(stream)