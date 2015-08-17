"""
Ssh wrapper for windows abova libssh c library and pyssh-types
"""
import time
import pyssh
import re

class Wssh():
    """Ssh wrapper for windows"""
    
    def __init__(self, host,  name,  password=''):
        self.host=host
        """ip or dns of host for communication"""
        self.name = name
        """login name for ssh connection"""
        self.password = password
        """password name for ssh connection"""
        self.ssh = None
        """Ssh subprocessed instance"""
        self.sftp = None
        """Sftp subprocessed instance"""
        self._buffer = ""
        self._prefix = ""        
        
    def connect(self):
        """connect session"""
        s = pyssh.new_session(hostname=self.host, username=self.name, password=self.password)
        self.ssh = s.create_shell()
        self.sftp = s.create_sftp()
        self._prefix = ""
        self._read_prefix()
        i=0        
        while len(self._prefix) == 0 and i < 10:
            self._read_prefix()
            i += 1
        self._clear()

    def cd(self, dir):
        """ssh cd"""
        self.ssh.write("cd " + dir + "\n")
        self._read_prefix()
        if len(self._prefix) == 0:
            time.sleep(2)
            self._read_prefix()
        return self._read_filter("cd " + dir)
    
    def pwd(self):
        """ssh pwd"""
        self.ssh.write("pwd\n")        
        return self._read_filter("pwd")
    
    def mkdir(self, dir):
        """ssh cd"""
        self.ssh.write("mkdir " + dir + "\n")        
        return _read_filter("mkdir " + dir)

    def put(self, file, dest_dir=None):
        """sftp put"""

    def put_r(self, dir, dest_dir=None):
        """sftp put -r"""

    def exec_(self, command):
        """run async command"""
        self.ssh.write(command + "\n")        
        text = self._read_filter(command)
        self._clear()
        return text

    def write(self, text):
        """write text to stdin"""
        self.ssh.write(text + "\n")

    def read(self, timeout, echo=None):
        """read text from stdout"""
        len_buffer = len(self._buffer)
        sec = time.time() + timeout
        text = self._read()
        while len_buffer == len(text) and sec < time.time():
            text += self._read()
        len_buffer = text
        text = self._read_filter(echo)
        return text

    def _clear(self):
        """read std in and drop it"""
        byte = b"p"
        while len(byte) > 0:
            byte = self.ssh.read(100)
        self._buffer = ""

    def _read_filter(self, echo=None):
        """read text without echo and prefix from std in"""
        text = self._read()
        res = []
        if echo is not None:
            e = re.match( '(' + echo + '\r\n\x1b]0;)', text)
            if e is None:
                e = re.match( '(' + echo + ')', text)
            if e is not None:
                text = text[len(e.group(1)):]
        while len(text) > 0:
            prefix = True
            while prefix is not None:
                prefix = re.match( '\s*(' + self._prefix + '\$\s*)', text)
                if prefix is None:
                    prefix = re.match( '\s*(' + self._prefix + '\x07\s*)', text)
                if prefix is not None:
                    text = text[len(prefix.group(1)):]
            line = re.match('(.*)(\r\nx1b]0;)', text)
            if line is None:                    
                line = prefix = re.match( '(.*)(\r\n)', text)
            if line is None:                    
                line = prefix = re.match( '(.*\S)(.*)$', text)
            if line is not None:
                if len(line.group(1)) > 0:
                    res.append(line.group(1))
                text = text[len(line.group(1))+len(line.group(2)):]
        if len(res) == 0:
            return ""
        return "\n".join(res)

    def _read(self):
        """read std in"""
        text = self._buffer
        self._buffer = ""
        text_hlp = ""
        i = 0
        while i<3:
            text_hlp = self.ssh.read(100).decode("utf8")
            if(len(text_hlp)>0):
                text += text_hlp
                i = 0
            else:
                i += 1
                time.sleep(1)
        return text

    def _read_prefix(self):
        """filter std in"""
        text = self._read()
        self._buffer += text
        prefix = re.search( '(' + self.name + '@\S*:)\s*(~[^@:]*)\$', text)
        if prefix is not None:
            self._prefix = prefix.group(1) + '\s*' + prefix.group(2)
        else:
            self._prefix = ""
            
        
        
            