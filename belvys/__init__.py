"""Getting data from Kisters' portfolio management system 'Belvis'."""

from . import _version, adjustment
from .api import Api
from .example import (
    example_api,
    example_api_to_file,
    example_structure,
    example_structure_to_file,
)
from .structure import Structure, Ts, TsTree
from .tenant import Tenant

__version__ = _version.get_versions()["version"]
