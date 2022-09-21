"""Getting data from Kisters' portfolio management system 'Belvis'."""

from . import _version, adjustment
from .api import Api
from .structure import Structure, TsTree, Ts
from .tenant import Tenant
from .example import (
    example_structure,
    example_structure_to_file,
    example_api,
    example_api_to_file,
)

__version__ = _version.get_versions()["version"]
