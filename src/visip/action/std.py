import os
import io
import attr
import subprocess

from typing import *
from ..dev import base, exceptions as exc
from ..dev import dtype, data
from ..code import decorators


@decorators.Enum
class FileMode:
    read = 0
    write = 1

Folder = NewType('Folder', str)

@attr.s(auto_attribs=True)
class File(dtype.DataClassBase):
    """
    Represent a file.
    TODO: In fact we need to represent only already existiong input files.
    The output files are just path, no hash. So possibly define these
    two as separate types.
    """
    path: str
    mode: FileMode
    hash: int

    def __str__(self):
        return self.path

@attr.s(auto_attribs=True)
class ExecResult(dtype.DataClassBase):
    args: List[str]
    return_code: int
    workdir: Folder
    stdout: str
    stderr: str


@decorators.action_def
def file_r(path: str, workspace: Folder = "") -> File:
    # we assume to be in the root of the VISIP workspace
    full_path = os.path.join(workspace, path)
    # path relative to the root
    if os.path.isfile(full_path):
        return File(path=full_path, mode=FileMode.read, hash=data.hash_file(full_path))
    else:
        raise exc.ExcVFileNotFound(full_path)


@decorators.action_def
def file_w(path: str, workspace: Folder = "") -> File:
    # we assume to be in the root of the VISIP workspace
    full_path = os.path.join(workspace, path)
    # path relative to the root
    if os.path.isfile(full_path):
        raise exc.ExcVWrongFileMode("Existing output file: " + full_path)
    else:
        return File(path=full_path, mode=FileMode.write, hash=None)




@decorators.Enum
class SysFile:
    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL


Command = NewType('Command', List[Union[str, File]])
Redirection = NewType('Redirection', Union[File, None, SysFile])

def _subprocess_handle(redirection):
    if type(redirection) is File:
        if redirection.mode != FileMode.write:
            raise exc.ExcVWrongFileMode("An output file requested as the target for redirection.")
        return open(redirection.path, "w")
    return redirection


@decorators.action_def
def system(arguments: Command, stdout: Redirection = None, stderr: Redirection = None) -> ExecResult:
    """
    Execute a system command.  No support for portability.
    The files in the 'arguments' are converted to the file names.
    arguments[0] is the command path.
    Commmand line is composed from the (quoted) arguments separated by the space.
    See: [Subprocess doc](https://docs.python.org/3/library/subprocess.html)

    TODO: Some support for piped actions, i.e. when one action produce a sequence of values, we can process them
    in pipline fassin. Here we can treat stdout as a sequence of lines and thus pipe them to other process
    through the POpen piping.
    """
    subprocess.PIPE
    args = [str(arg) for arg in arguments]
    stdout = _subprocess_handle(stdout)
    stderr = _subprocess_handle(stderr)
    result = subprocess.run(args, stdout=stdout, stderr=stderr)
    exec_result = ExecResult(
        args=args,
        return_code=result.returncode,
        workdir=os.getcwd(),
        stdout=result.stdout,
        stderr=result.stderr
    )
    try:
        stdout.close()
    except AttributeError:
        pass
    return exec_result




#
# def system_script(commands: List[Command]):
#     pass