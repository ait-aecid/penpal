"""
vncexecutor.py
============================================
This class enables executing commands via vnc.
It utilizes the vncdotool. https://github.com/sibson/vncdotool (can be installed with pip)

the vnc client connection_string needs to be in the format address[:display|::port]

"""

from attackmate.executors.baseexecutor import BaseExecutor
from attackmate.execexception import ExecException
from attackmate.result import Result
from attackmate.variablestore import VariableStore
from attackmate.processmanager import ProcessManager
from attackmate.schemas.vnc import VncCommand
from vncdotool import api
from vncdotool.client import AuthenticationError
from attackmate.executors.vnc.sessionstore import SessionStore


class VncExecutor(BaseExecutor):
    def __init__(self, pm: ProcessManager, cmdconfig=None, *, varstore: VariableStore):
        self.session_store = SessionStore()
        self.set_defaults()
        super().__init__(pm, varstore, cmdconfig)

    def set_defaults(self):
        self.hostname = None
        self.port = None
        self.display = None
        self.password = None

    def connect(self, command: VncCommand) -> api.ThreadedVNCClientProxy:
        connection_string = self.hostname

        if self.display is not None:
            connection_string += f':{self.display}'
        if self.port is not None:
            if self.display is None:
                connection_string += f'::{self.port}'

        client = api.connect(connection_string, command.password)

        return client

    def connect_use_session(self, command):

        if command.creates_session is not None:
            # If 'creates_session' is specified, create a new session and save it
            client = self.connect(command)
            self.session_store.set_session(command.creates_session, client)
            return client

        if command.session is not None:
            # If 'session' is specified, check if it exists, else raise an error
            if not self.session_store.has_session(command.session):
                raise ExecException(f'VNC-Session not in Session-Store: {command.session}')
            else:
                return self.session_store.get_client_by_session(command.session)

        # If neither 'creates_session' nor 'session' is provided
        default_session = 'default'

        if not self.session_store.has_session(default_session):
            # Create default session if it doesn't exist
            client = self.connect(command)
            self.session_store.set_session(default_session, client)
        else:
            # Retrieve the default session if it already exists
            client = self.session_store.get_client_by_session(default_session)

        return client

    def cache_settings(self, command: VncCommand):
        if command.hostname:
            self.hostname = command.hostname
        if command.port:
            self.port = command.port
        if command.display:
            self.display = command.display
        if command.password:
            self.password = command.password

    def log_command(self, command: VncCommand):
        self.cache_settings(command)
        self.logger.info(f"Executing Vnc-Command: '{command.cmd}'. Host: {self.hostname}")

    def send_keys(self, client, keys):
        for k in keys:
            client.keyPress(k)

    def _exec_cmd(self, command: VncCommand) -> Result:
        self.cache_settings(command)

        try:
            client = self.connect_use_session(command)
            if command.cmd == 'key' and command.key:
                client.keyPress(command.key)
            elif command.cmd == 'type' and command.input:
                self.send_keys(client, command.input)
            elif command.cmd == 'move':
                client.mouseMove(command.x, command.y)
            elif command.cmd == 'capture':
                client.captureScreen(command.filename)
            elif command.cmd == 'click':
                client.mousePress(1)
            elif command.cmd == 'expectscreen':
                client.expectScreen(command.filename, command.maxrms)
        except ValueError as e:
            raise ExecException(e)
        except AttributeError as e:
            raise ExecException(e)
        except AuthenticationError as e:
            raise ExecException(e)
        except OSError as e:
            raise ExecException(e)

        output = ''
        return Result(output, 0)
