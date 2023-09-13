import logging
from attackmate.cmdvars import CmdVars

from attackmate.exitonerror import ExitOnError
from attackmate.looper import Looper
from .result import Result
from .execexception import ExecException
from .schemas import BaseCommand, CommandConfig
from .conditional import Conditional
from .variablestore import VariableStore
from typing import Any


class BaseExecutor(ExitOnError, CmdVars, Looper):
    """

    The BaseExecutor is the base class of all Executors.
    It enables base functionality for all Executors and
    provides a structure for all Executors.

    In order to create a custom Executor, one must simply
    derive from the BaseExecutor and implement the method
    _exec_cmd()

    """
    def __init__(self, variablestore: VariableStore, cmdconfig=CommandConfig()):
        """ Constructor for BaseExecutor

        Parameters
        ----------
        cmdconfig : str, default `None`
            cmd_config settings.

        """
        CmdVars.__init__(self, variablestore)
        ExitOnError.__init__(self)
        Looper.__init__(self, cmdconfig)
        self.logger = logging.getLogger('playbook')
        self.cmdconfig = cmdconfig
        self.output = logging.getLogger("output")

    def run(self, command: BaseCommand):
        """ Execute the command

        This method is executed by AttackMate and
        executes the given command. This method sets the
        run_count to 1 and runs the method exec(). Please note
        that this function will exchange all variables of the BaseCommand
        with the values of the VariableStore!

        Parameters
        ----------
        command : BaseCommand
            The settings for the command to execute

        """
        if command.only_if:
            if not Conditional.test(self.varstore.substitute(command.only_if, True)):
                if hasattr(command, "type"):
                    self.logger.warn(f"Skipping {command.type}: {command.cmd}")
                else:
                    self.logger.warn(f"Skipping {command.cmd}")
                return
        self.reset_run_count()
        self.logger.debug(f"Template-Command: '{command.cmd}'")
        self.exec(self.replace_variables(command))

    def log_command(self, command):
        """ Log starting-status of the command

        """
        self.logger.info(f"Executing '{command}'")

    def save_output(self, command: BaseCommand, result: Result):
        """ Save output of command to a file. This method will
            ignore all exceptions and won't stop the programm
            on error.
        """
        if command.save:
            try:
                with open(command.save, "w") as outfile:
                    outfile.write(result.stdout)
            except Exception as e:
                self.logger.warn(f"Unable to write output to file {command.save}: {e}")

    def exec(self, command: BaseCommand):
        try:
            self.log_command(command)
            result = self._exec_cmd(command)
        except ExecException as error:
            result = Result(error, 1)
        self.exit_on_error(command, result)
        self.set_result_vars(result)
        self.output.info(f"Command: {command.cmd}\n{result.stdout}")
        self.save_output(command, result)
        self.error_if_or_not(command, result)
        self.loop_if(command, result)
        self.loop_if_not(command, result)

    def _loop_exec(self, command: BaseCommand):
        self.exec(command)

    def _exec_cmd(self, command: Any) -> Result:
        return Result(None, None)
