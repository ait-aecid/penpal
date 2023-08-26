"""
tempfileexecutor.py
============================================
Creates temporary files and directories
"""

import tempfile
from typing import Any
from .baseexecutor import BaseExecutor, Result
from .schemas import TempfileCommand
from .variablestore import VariableStore


class TempfileExecutor(BaseExecutor):
    def __init__(self, varstore: VariableStore, cmdconfig=None):
        self.tempfilestore: dict[str, Any] = {}
        super().__init__(varstore, cmdconfig)

    def log_command(self, command: TempfileCommand):
        if command.isdir:
            self.logger.warn("Creating temporary directory..")
        else:
            self.logger.warn("Creating temporary file..")

    def _exec_cmd(self, command: TempfileCommand) -> Result:
        ret = 0
        fullpath = ""
        if command.isdir:
            tmpfile = tempfile.TemporaryDirectory()
            self.tempfilestore[command.variable] = tmpfile
            fullpath = tmpfile.name
        else:
            tmpdir = tempfile.NamedTemporaryFile()
            self.tempfilestore[command.variable] = tmpdir
            fullpath = tmpdir.name

        self.varstore.set_variable(command.variable, fullpath)

        return Result(fullpath, ret)
