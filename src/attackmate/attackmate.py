"""AttackMate reads a playbook and executes the attack

A playbook stored in a dictionary with a list of attacks. Attacks
are executed by "Executors". There are many different
Executors like: ShellExecutor, SleepExecutor or MsfModuleExecutor
This class creates instances of all possible Executors, iterates
over all attacks and runs the specific Executor with the given
configuration.
"""

import logging
import attackmate.executors as executors
from attackmate.schemas.config import Config
from attackmate.schemas.playbook import Playbook, Commands
from .variablestore import VariableStore
from .processmanager import ProcessManager


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
        self.initialize_variable_parser()
        self.initialize_executors()

    def initialize_variable_parser(self):
        """Initializes the variable-parser

        The variablestore stores and replaces variables with values in certain strings
        """
        self.varstore = VariableStore()
        self.varstore.from_dict(self.playbook.vars)

    def initialize_executors(self):
        """Initialize all Executors

        Executors are supposed to execute commands. This method initializes
        all possible executors.

        """
        self.msfsessionstore = executors.MsfSessionStore(self.varstore)
        init_args = {
            'pm': self.pm,
            'varstore': self.varstore,
            'cmdconfig': self.pyconfig.cmd_config,
        }

        # same executor instance for ssh and sftp commands
        ssh_executor = executors.SSHExecutor(**init_args)

        self.executors = {
            'shell': executors.ShellExecutor(**init_args),
            'ssh': ssh_executor,
            'sftp': ssh_executor,
            'msf-session': executors.MsfSessionExecutor(
                **init_args, msfconfig=self.pyconfig.msf_config, msfsessionstore=self.msfsessionstore
            ),
            'msf-payload': executors.MsfPayloadExecutor(**init_args, msfconfig=self.pyconfig.msf_config),
            'msf-module': executors.MsfModuleExecutor(
                **init_args, msfconfig=self.pyconfig.msf_config, msfsessionstore=self.msfsessionstore
            ),
            'sliver': executors.SliverExecutor(**init_args, sliver_config=self.pyconfig.sliver_config),
            'sliver-session': executors.SliverSessionExecutor(
                **init_args, sliver_config=self.pyconfig.sliver_config
            ),
            'father': executors.FatherExecutor(**init_args),
            'webserv': executors.WebServExecutor(**init_args),
            'http-client': executors.HttpClientExecutor(**init_args),
            'setvar': executors.SetVarExecutor(**init_args),
            'sleep': executors.SleepExecutor(**init_args),
            'mktemp': executors.TempfileExecutor(**init_args),
            'debug': executors.DebugExecutor(**init_args),
            'include': executors.IncludeExecutor(**init_args, runfunc=self.run_commands),
            'loop': executors.LoopExecutor(**init_args, runfunc=self.run_commands),
            'regex': executors.RegExExecutor(**init_args),
            'vnc': executors.VncExecutor(**init_args),
        }

    def run_commands(self, commands: Commands):
        """Pass commands to the executors

        This function interates over all configured
        commands and passes them to the executors.

        """
        for command in commands:
            executor = self.executors.get(command.type)
            if executor:
                executor.run(command)

    def main(self):
        """The main function

        Passes the main playbook-commands
        to run_commands

        """
        try:
            self.run_commands(self.playbook.commands)
            self.pm.kill_or_wait_processes()
        except KeyboardInterrupt:
            self.logger.warning('Program stopped manually')

        return 0
