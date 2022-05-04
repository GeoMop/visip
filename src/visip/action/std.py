import os
import io
import sys

import attr
import subprocess

from ..dev import base, exceptions as exc
from ..dev import data, dtype
from ..code import decorators
from ..dev import tools

# @decorators.Enum
# class FileMode:
#     read = 0
#     write = 1

Folder = dtype.NewType(dtype.Str, 'Folder')
FileOut = dtype.NewType(dtype.Str, 'FileOut')

@attr.s(auto_attribs=True)
class FileIn(dtype.DataClassBase):
    """
    Represent an existing input file.
    TODO: In fact we need to represent only already existiong input files.
    The output files are just path, no hash. So possibly define these
    two as separate types.
    """
    path: dtype.Str
    hash: dtype.from_typing(bytes)

    def __str__(self):
        return self.path

    def __hash__(self):
        return self.hash


@attr.s(auto_attribs=True)
class ExecResult(dtype.DataClassBase):
    args: dtype.List(dtype.Str)
    return_code: dtype.Int
    workdir: Folder
    stdout: dtype.Str  # Exists when result is available.
    stderr: dtype.Str


@decorators.action_def
def file_in(path: dtype.Str, workspace: Folder = "") -> FileIn:
    # we assume to be in the root of the VISIP workspace
    full_path = os.path.abspath(os.path.join(workspace, path))
    # path relative to the root
    if os.path.isfile(full_path):
        return FileIn(path=full_path, hash=data.hash_file(full_path))
    else:
        print("err cwd", os.getcwd())
        raise exc.ExcVFileNotFound(full_path)


@decorators.action_def
def file_out(path: dtype.Str, workspace: Folder = "") -> FileOut:
    # we assume to be in the root of the VISIP workspace
    full_path = os.path.join(workspace, path)
    # path relative to the root
    if os.path.isfile(full_path):
        raise exc.ExcVWrongFileMode("Existing output file: " + full_path)
    else:
        #return FileOut(full_path)
        return full_path



@decorators.Enum
class SysFile:
    PIPE = subprocess.PIPE
    STDOUT = subprocess.STDOUT
    DEVNULL = subprocess.DEVNULL


Command = dtype.NewType(dtype.List(dtype.Union(dtype.Str, dtype.from_typing(FileIn))), 'Command')
Redirection = dtype.NewType(dtype.Union(FileOut, dtype.NoneType, dtype.from_typing(SysFile)), 'Redirection')

def _subprocess_handle(redirection):
    if type(redirection) is str:    # TODO: should be FileOut
        return open(redirection, "w")
    return redirection


@decorators.action_def
def system(arguments: Command, stdout: Redirection = None, stderr: Redirection = None, workdir:dtype.Str = '') -> ExecResult:
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
    with tools.change_cwd(workdir):
        subprocess.PIPE
        args = [str(arg) for arg in arguments]
        stdout = _subprocess_handle(stdout)
        stderr = _subprocess_handle(stderr)
        #print("syscall: ", args)
        if sys.platform == 'win32':
            result = subprocess.run(args, stdout=stdout, stderr=stderr, shell=True) # solution from https://stackoverflow.com/questions/24306205/file-not-found-error-when-launching-a-subprocess-containing-piped-commands
        else:
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
            stderr.close()
        except AttributeError:
            pass
        if exec_result.return_code != 0:
            exc.ExcVCommandFailed(str(args), exec_result)

        return exec_result

@decorators.action_def
def derived_file(f: FileIn, ext:dtype.Str) -> FileOut:
    base, old_ext = os.path.splitext (f.path)
    new_file_name = base + ext
    return file_out.call(new_file_name)

@decorators.action_def
def format(format_str: dtype.Str, *args: dtype.Any) -> dtype.Str:
    return format_str.format(*args)

@decorators.action_def
def file_from_template(template: dtype.Const(dtype.from_typing(FileIn)),
                       parameters: dtype.Dict(dtype.Str, dtype.Str),
                       delimiters: dtype.Const(dtype.Str)= "<>") -> FileIn:
    """
    Substitute for placeholders of format '<name>' from the dict 'params'.
    :param file_in: Template file with extension '.tmpl'.
    :param file_out: Values substituted.
    :param params: { 'name': value, ...}
    """
    if os.path.splitext(template.path)[1] != ".tmpl":
        exc.ExcVFileNotFound("File template must have '.tmpl' extension, get path: {}".format(template.path))
    used_params = []
    with open(template.path, 'r') as src:
        text = src.read()
    for name, value in parameters.items():
        placeholder = '{}{}{}'.format(delimiters[0], name, delimiters[1])
        n_repl = text.count(placeholder)
        if n_repl > 0:
            used_params.append(name)
            text = text.replace(placeholder, str(value))
    file_out = derived_file.call(template, '')
    with open(file_out, 'w') as dst:
        dst.write(text)

    return file_in.call(file_out)

#
# def system_script(commands: List[Command]):
#     pass