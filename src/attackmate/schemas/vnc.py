from typing import Optional, Literal
from .base import BaseCommand, StringNumber
from pydantic import model_validator


class VncCommand(BaseCommand):
    type: Literal['vnc']
    cmd: Literal['key', 'type', 'move', 'capture', 'click', 'expectscreen']
    hostname: Optional[str] = None
    port: Optional[StringNumber] = None
    display: Optional[StringNumber] = None
    password: Optional[str] = None
    key: Optional[str] = None
    input: Optional[str] = None
    filename: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    creates_session: Optional[str] = None
    session: Optional[str] = None
    maxrms: Optional[float] = 0

    @model_validator(mode='after')
    def check_cmd_requirements(cls, values):
        cmd = values.cmd

        if values.creates_session is not None and values.session is not None:
            raise ValueError('Cannot specify both "creates_session" and "session" at the same time.')
        if cmd == 'type' and values.input is None:
            raise ValueError('Command "type" requires an "input" field.')
        elif cmd == 'key' and values.key is None:
            raise ValueError('Command "key" requires a "key" field.')
        elif cmd == 'capture' and values.filename is None:
            raise ValueError('Command "capture" requires a "filename" field.')
        elif cmd == 'expectscreen' and values.filename is None:
            raise ValueError('Command  "expectscreen" requires a "filename" field.')
        elif cmd == 'move':
            if values.x is None or values.y is None:
                raise ValueError('Command "move" requires both "x" and "y" fields.')

        return values
