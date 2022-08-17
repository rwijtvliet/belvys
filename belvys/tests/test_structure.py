import pathlib
from typing import Dict

import pytest
import yaml
from belvys import Structure


def id_fn(val) -> str:
    if isinstance(val, pathlib.Path):
        return val.name
    return val


def path(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / "test_structure_files" / f"{filename}.yaml"


def do_test(file: pathlib.Path, load_as: str):
    # Load as object, not from file.
    if load_as == "direct":
        data = yaml.load(open(file), Loader=yaml.FullLoader)
        _ = Structure(**data)

    # Load from file
    else:
        if load_as == "pathstring":
            file = str(file)
        _ = Structure.from_file(file)


@pytest.mark.parametrize("load_as", ["direct", "pathstring", "filepath"])
@pytest.mark.parametrize(
    "file",
    [
        path("missing_freq"),
        path("missing_tz"),
        path("missing_pflines_1"),
        path("missing_pflines_2"),
        path("missing_portfolios_1"),
        path("missing_portfolios_2"),
        path("missing_portfolios_3"),
        path("missing_prices_1"),
        path("missing_prices_2"),
        path("missing_prices_3"),
        path("missing_prices_4"),
        path("incorrect_sythetic_reference_1"),
        path("incorrect_sythetic_reference_2"),
    ],
    ids=id_fn,
)
def test_nok(file: pathlib.Path, load_as: str):
    """Test if incorrect structure files are correctly rejected."""
    with pytest.raises(Exception):
        do_test(file, load_as)


@pytest.mark.parametrize("load_as", ["direct", "pathstring", "filepath"])
@pytest.mark.parametrize(
    "file",
    [
        path("ok_basic"),
        path("ok_basic_2"),
        path("ok_complex"),
    ],
    ids=id_fn,
)
def test_ok(file: pathlib.Path, load_as: str):
    """Test if correct structure files are correctly accepted."""
    do_test(file, load_as)


@pytest.mark.parametrize(
    "file",
    [
        path("check_expansion_1"),
        path("check_expansion_2"),
        path("check_expansion_3"),
    ],
    ids=id_fn,
)
def test_ok_expansion(file: pathlib.Path):
    structure = Structure.from_file(file)

    def assert_equality(obj1, obj2):
        if isinstance(obj1, Dict):
            # assume all keys are strings, and all values are strings, lists of strings, or other dictionaries.
            assert set(obj1.keys()) == set(obj2.keys())
            for key in obj1:
                assert_equality(obj1[key], obj2[key])
        elif isinstance(obj1, str):
            assert obj1 == obj2
        else:  # list of strings
            assert set(obj1) == set(obj2)

    assert_equality(
        structure.pflines["sourced_by_market_1"],
        structure.pflines["forward_sourced"],
    )
    assert_equality(
        structure.pflines["sourced_by_market_2"]["forward"],
        structure.pflines["forward_sourced"],
    )
    assert_equality(
        structure.pflines["sourced_by_market_3"]["layer1"],
        structure.pflines["sourced_by_market_2"],
    )
    assert_equality(
        structure.pflines["sourced_by_market_3"]["layer1"]["forward"],
        structure.pflines["forward_sourced"],
    )
