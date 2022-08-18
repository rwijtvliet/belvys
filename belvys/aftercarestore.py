"""Collection of aftercare functions."""


import datetime as dt
from typing import Callable, Iterable, Union

import pandas as pd
import portfolyo as pf

Aftercare = Callable[[pd.Series, int, str, str], pd.Series]


def fixed_to_float(fixed: str) -> Aftercare:
    """
    Use if: api returns series with frequency in incorrect (fixed) timezone.

    Parameters
    ----------
    fixed : str
        The timezone (UTC-offset) that the values should be interpreted in.
    tsids : Iterable[int], optional
        Id(s) of timeseries this function should change. Leaves others unchanged. If
        None: apply to all timeseries.

    Returns
    -------
    Aftercare function

    Example
    -------
    The following timeseries has UTC timestamps but denote the start of a day in the CET
    timezone:

    2022-08-16 23:00:00+00:00      226.047
    2022-08-17 23:00:00+00:00      226.068

    The function ``fn = fixed_to_float("+01:00")`` turns it into

    2022-08-17 00:00:00      226.047
    2022-08-18 00:00:00      226.068
    """

    def aftercare(s: pd.Series, *args) -> pd.Series:
        return s.tz_convert(fixed).tz_localize(None)

    return aftercare


def cet_to_float(target_tsid: Union[int, Iterable[int]]) -> Aftercare:
    return fixed_to_float(target_tsid, "+01:00")


def cet_to_Berlin() -> Aftercare:
    def aftercare(s: pd.Series, *args) -> pd.Series:
        return s.tz_convert("+01:00").tz_localize(None).tz_convert("Europe/Berlin")

    return aftercare


def standardize_belvis(tz) -> Aftercare:
    def aftercare(s: pd.Series, *args) -> pd.Series:
        td = s.index[1] - s.index[0]
        if td <= dt.timedelta(hours=2):
            bound = "right"
        else:
            bound = "left"
        return pf.standardize(s, "aware", bound, tz=tz, floating=False)

    return aftercare
