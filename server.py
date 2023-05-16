import paramiko
from cmd import Cmd
from abc import ABC, abstractmethod
from sys import platform
import socket, threading
class ServerBase(ABC):

    def __init__(self):
        # create a multithreaded event, which is basically a
        # thread-safe boolean
        self._is_running = threading.Event()

        # this socket will be used to listen to incoming connections
        self._socket = None

        # this will contain the shell for the connected client.
        # we don't yet initialize it, since we need to get the
        # stdin and stdout objects after the connection is made.
        self.client_shell = None

        # this will contain the thread that will listen for incoming
        # connections and data.
        self._listen_thread = None

    # To start the server, we open the socket and create 
    # the listening thread.
    def start(self, address='localhost', port=12750, timeout=1):
        if not self._is_running.is_set():
            self._is_running.set()

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

            # reuse port is not avaible on windows
            if platform == "linux" or platform == "linux2":
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

            self._socket.settimeout(timeout)
            self._socket.bind((address, port))

            self._listen_thread = threading.Thread(target=self._listen)
            self._listen_thread.start()

    # To stop the server, we must join the listen thread
    # and close the socket.
    def stop(self):
        if self._is_running.is_set():
            self._is_running.clear()
            self._listen_thread.join()
            self._socket.close()

    # The listen function will constantly run if the server is running.
    # We wait for a connection, if a connection is made, we will call 
    # our connection function.
    def _listen(self):
        while self._is_running.is_set():
            try:
                self._socket.listen()
                client, addr = self._socket.accept()
                self.connection_function(client)
            except socket.timeout:
                pass

    @abstractmethod
    def connection_function(self, client):
        pass
class Shell(Cmd):

    # Message to be output when cmdloop() is called.
    intro='Amin SSH Shell'

    use_rawinput=False

    prompt='My Shell> '

    def __init__(self, stdin=None, stdout=None):
        super(Shell, self).__init__(completekey='tab', stdin=stdin, stdout=stdout)

    def print(self, value):
        if self.stdout and not self.stdout.closed:
            self.stdout.write(value)
            self.stdout.flush()

    def printline(self, value):
        self.print(value + '\r\n')
    def do_greet(self, arg):
        if arg:
            self.printline('Hey {0}! Nice to see you!'.format(arg))
        else:
            self.printline('Hello there!')

    def do_bye(self, arg):
        self.printline('See you later!')

        return True

    def emptyline(self):
        self.print('\r\n')
class SshServerInterface(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_auth_password(self, username, password):
        if (username == 'admin') and (password == 'password'):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_banner(self):
        return ('Amin SSH Server\r\n', 'en-US')
class SshServer(ServerBase):

    def __init__(self, host_key_file, host_key_file_password=None):
        super(SshServer, self).__init__()

        self._host_key = paramiko.RSAKey.from_private_key_file(host_key_file, host_key_file_password)

    def connection_function(self, client):
        try:
            session = paramiko.Transport(client)
            session.add_server_key(self._host_key)

            server = SshServerInterface()
            try:
                session.start_server(server=server)
            except paramiko.SSHException:
                return

            channel = session.accept()
            stdio = channel.makefile('rwU')

            self.client_shell = Shell(stdio, stdio)
            self.client_shell.cmdloop()

            session.close()
        except:
            pass
if __name__ == '__main__':
    server = SshServer('../../.ssh/id_rsa', "pass")
    server.start()