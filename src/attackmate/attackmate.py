"""AttackMate reads a playbook and executes the attack

A playbook stored in a dictionary with a list of attacks. Attacks
are executed by "Executors". There are many different
Executors like: ShellExecutor, SleepExecutor or MsfModuleExecutor
This class creates instances of all possible Executors, iterates
over all attacks and runs the specific Executor with the given
configuration.
"""

from typing import Dict
import logging
from attackmate.result import Result
import attackmate.executors as executors
from attackmate.schemas.config import Config
from attackmate.schemas.playbook import Playbook, Commands, Command
from .variablestore import VariableStore
from .processmanager import ProcessManager
from attackmate.executors.baseexecutor import BaseExecutor
from attackmate.executors.executor_factory import executor_factory


class AttackMate:
    def __init__(self, playbook: Playbook, config: Config) -> None:
        """Constructor for AttackMate

        This constructor initializes the logger('playbook'), the playbook,
        the variable-parser and all the executors.

        Parameters
        ----------
        config_file : str
            The path to a yaml-playbook
        """
        self.logger = logging.getLogger('playbook')
        self.pm = ProcessManager()
        self.pyconfig = config
        self.playbook = playbook
        self._initialize_variable_parser()
        self.msfsessionstore = executors.MsfSessionStore(self.varstore)
        self.executor_config = self._get_executor_config()
        self.executors: Dict[str, BaseExecutor] = {}

    def _initialize_variable_parser(self):
        """Initializes the variable-parser

        The variablestore stores and replaces variables with values in certain strings
        """
        self.varstore = VariableStore()
        self.varstore.from_dict(self.playbook.vars)
        self.varstore.replace_with_prefixed_env_vars()

    def _get_executor_config(self) -> dict:
        config = {
            'pm': self.pm,
            'varstore': self.varstore,
            'cmdconfig': self.pyconfig.cmd_config,
            'msfconfig': self.pyconfig.msf_config,
            'msfsessionstore': self.msfsessionstore,
            'sliver_config': self.pyconfig.sliver_config,
            'runfunc': self._run_commands,
        }
        return config

    def _get_executor(self, command_type: str) -> BaseExecutor:
        if command_type not in self.executors:
            self.executors[command_type] = executor_factory.create_executor(
                command_type, **self.executor_config
            )

        return self.executors[command_type]

    def _run_commands(self, commands: Commands):
        for command in commands:
            command_type = 'ssh' if command.type == 'sftp' else command.type
            executor = self._get_executor(command_type)
            if executor:
                executor.run(command)

    def run_command(self, command: Command) -> Result:
        command_type = 'ssh' if command.type == 'sftp' else command.type
        executor = self._get_executor(command_type)
        if executor:
            result = executor.run(command)
        return result if result else Result(None, None)

    def main(self):
        """The main function

        Passes the main playbook-commands
        to run_commands

        """
        try:
            self._run_commands(self.playbook.commands)
            self.pm.kill_or_wait_processes()
        except KeyboardInterrupt:
            self.logger.warning('Program stopped manually')

        return 0
