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

HashValue = NewType('HashValue', int)

default_hash_fn = hash
def my_hash(x, seed=0):
    return default_hash_fn((x, seed))

hasher_fn = my_hash
def hash_stream(stream: bytearray, previous:HashValue=0) -> HashValue:
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

def hash(data, previous=0):
    return hash_stream(str(data), previous)


def hash_file(file_path):
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    sha1 = hashlib.sha1()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return hash(sha1.digest())


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