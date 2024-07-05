"""Getting data from Kisters' portfolio management system 'Belvis'."""

# import importlib.metadata
from . import adjustment  # noqa
from . import _version
from .api import Api  # noqa
from .example import (
    example_api,
    example_api_to_file,
    example_structure,
    example_structure_to_file,
)
from .structure import Structure, Ts, TsTree
from .tenant import Tenant

__version__ = _version.get_versions()["version"]
# __version__ = importlib.metadata.version(__package__ or __name__)
