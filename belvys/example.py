import pathlib
import shutil
from typing import Union

from .api import Api
from .structure import Structure


def _example_filepath(obj: str, which: str) -> pathlib.Path:
    """Location of example file."""
    filename = f"example_{obj}_{which}.yaml"
    path = pathlib.Path(__file__).parent / filename
    if not path.exists():
        raise FileNotFoundError(f"No file found at this path: {path}")
    return path


def _checked_filepath(filepath: Union[str, pathlib.Path]) -> pathlib.Path:
    """Correct and check filepath."""
    if isinstance(filepath, str):
        filepath = pathlib.Path(filepath)
    if not filepath.isfile():
        raise ValueError("Must specify path to a file.")
    elif filepath.exists():
        raise ValueError("File already exists; delete first.")
    return filepath


def example_structure(which: str = "basic") -> Structure:
    """Example instance of Structure class.

    Parameters
    ----------
    which : {'basic' (default), 'complex'}
        Which example to load.

    Returns
    -------
    Structure
    """
    return Structure.from_file(_example_filepath("structure", which))


def example_api(which: str = "basic") -> Api:
    """Example instance of Api class.

    Parameters
    ----------
    which : {'basic' (default), 'complex'}
        Which example to load.

    Returns
    -------
    Api
    """
    return Api.from_file(_example_filepath("api", which))


def example_structure_to_file(
    filepath: Union[str, pathlib.Path], which: str = "basic"
) -> None:
    """Save an example of a structure configuration to file.

    Parameters
    ----------
    path : Union[str, pathlib.Path]
        Path to save the file to.
    which : {'basic' (default), 'complex'}
        Which example to save.
    """
    shutil.copy(_example_filepath("structure", which), _checked_filepath(filepath))


def example_api_to_file(
    filepath: Union[str, pathlib.Path], which: str = "basic"
) -> None:
    """Save an example of an api configuration to file.

    Parameters
    ----------
    path : Union[str, pathlib.Path]
        Path to save the file to.
    which : {'basic' (default), 'complex'}
        Which example to save.
    """
    shutil.copy(_example_filepath("api", which), _checked_filepath(filepath))
