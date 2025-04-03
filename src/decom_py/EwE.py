import clr
import sys
import os
from pathlib import Path

class EwE:
    
    def __init__(self, ewe_dir):

        self._ewe_dir = Path(ewe_dir)
        if not self._ewe_dir.exists():
            raise FileNotFoundError(self._ewe_dir)

        self._ewe_core_path = self._ewe_dir.joinpath('EwECore.dll')
        if not self._ewe_core_path.exists():
            raise FileNotFoundError(self._ewe_core_path)

        clr.AddReference(str(self._ewe_core_path))

        self._ewe_core = __import__('EwECore')

    def core(self):
        return self._ewe_core.cCore()
