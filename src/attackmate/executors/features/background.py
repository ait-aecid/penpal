from attackmate.schemas.base import BaseCommand
from attackmate.processmanager import ProcessManager
from attackmate.result import Result
from multiprocessing import Queue
from multiprocessing.managers import SyncManager
from typing import Any, Optional
import logging


class Background:
    def __getstate__(self):
        """
        pm contains the states of the processes.
        This environment must not be in the subprocess!
        """
        state = self.__dict__.copy()
        state['pm'] = None
        state['manager'] = None
        return state

    def __init__(self, pm: ProcessManager):
        self.logger = logging.getLogger('playbook')
        self.pm = pm
        self.is_child_proc = False
        self.child_queue: Optional[Queue] = None
        self.manager: Optional[SyncManager] = None

    def _create_queue(self) -> Optional[Queue]:
        return None

    def exec_background(self, command: BaseCommand) -> Result:
        self.logger.info(f'Run in background: {getattr(command, "type", "")}({command.cmd})')

        queue = self._create_queue()

        if queue:
            p = self.pm.ctx.Process(target=self._exec_bg_cmd, args=(command, queue))
        else:
            p = self.pm.ctx.Process(target=self._exec_bg_cmd, args=(command,))
        p.start()
        p.join(5)
        self.pm.add_process(p, command.kill_on_exit)
        # background commands always return None Result
        return Result(None, None)

    def _exec_bg_cmd(self, command: Any, queue: Optional[Queue] = None):
        self.is_child_proc = True
        if queue:
            self.child_queue = queue
        self.exec(command)

    def _exec_cmd(self, command: Any) -> Result:
        return Result(None, None)

    def exec(self, command: BaseCommand):
        self._exec_cmd(command)
