"""Getting data from Kisters' portfolio management system 'Belvis'."""

from .tenant import Tenant
from .api import Api
from .structure import Structure

from .user_facing import example_structure, example_structure_to_file

from . import _version

__version__ = _version.get_versions()["version"]
