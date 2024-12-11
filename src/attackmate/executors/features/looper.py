import re
import time
import logging
from attackmate.executors.features.cmdvars import CmdVars
from attackmate.result import Result
from attackmate.schemas.base import BaseCommand
from attackmate.schemas.config import CommandConfig


class Looper:
    def __init__(self, cmdconfig: CommandConfig):
        self.logger = logging.getLogger('playbook')
        self.cmdconfig = cmdconfig
        self.reset_run_count()

    def _loop_exec(self, command: BaseCommand):
        err_str = f'loop_exec for command {getattr(command, "type", "")} is not implemented!'
        self.logger.error(err_str)
        exit(1)

    def reset_run_count(self):
        self.run_count = 1

    def loop_if(self, command: BaseCommand, result: Result):
        if command.loop_if and (match := re.search(command.loop_if, result.stdout, re.MULTILINE)):
            self.logger.warning(f'Re-run command because loop_if matches: {match.group(0)}')
            if self.run_count < CmdVars.variable_to_int('loop_count', command.loop_count):
                self.run_count += 1
                time.sleep(self.cmdconfig.loop_sleep)
                self._loop_exec(command)
            else:
                self.logger.error('Exiting because loop_count exceeded')
                exit(1)
        else:
            self.logger.debug('loop_if does not match')

    def loop_if_not(self, command: BaseCommand, result: Result):
        if command.loop_if_not and re.search(command.loop_if_not, result.stdout, re.MULTILINE) is None:
            self.logger.warning('Re-run command because loop_if_not does not match')

            if self.run_count < CmdVars.variable_to_int('loop_count', command.loop_count):
                self.run_count += 1
                time.sleep(self.cmdconfig.loop_sleep)
                self._loop_exec(command)
            else:
                self.logger.error('Exiting because loop_count exceeded')
                exit(1)
        else:
            self.logger.debug('loop_if_not does not match')
