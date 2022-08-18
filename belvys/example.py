import pathlib
import shutil
from typing import Union

from .structure import Structure


def example_filepath(which: str) -> pathlib.Path:
    """Returns location of example file."""
    filename = f"structure_example_{which}.yaml"
    path = pathlib.Path(__file__).parent / filename
    if not path.exists():
        raise FileNotFoundError(f"No file found at this path: {path}")
    return path


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
    return Structure.from_file(example_filepath(which))


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
    if isinstance(filepath, str):
        filepath = pathlib.Path(filepath)
    if not filepath.isfile():
        raise ValueError("Must specify path to a file.")
    elif filepath.exists():
        raise ValueError("File already exists; delete first.")
    shutil.copy(example_filepath(which), filepath)
