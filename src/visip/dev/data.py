"""
Functions for uniform manipulation of the data. These functions treat the basic types and all attr classes.
We support:
- representation
- serialization into a bytearray
- deserialization from a byte array
- hash

Same special dataclasses are implemented, in particular:
- file wrapper
- ...
"""
from typing import NewType



HashValue = NewType('HashValue', int)

default_hash_fn = hash
def my_hash(x, seed=0):
    return default_hash_fn((x, seed))

hasher_fn = my_hash
def hash(stream: bytearray, previous:HashValue=0) -> HashValue:
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


def serialize(data):
    """
    Serialize a data tree 'data' into a byte array.
    :param data:
    :return:
    """


def deserialize(stream: bytearray):
    """
    Deserialize a data tree.
    :param stream:
    :return:
    """