"""Collection of adjustment functions."""


import datetime as dt
from typing import Callable

import pandas as pd
import portfolyo as pf

Adjustment = Callable[[pd.Series, int, str, str], pd.Series]
Adjustment = Callable[[pd.Series], pd.Series]


def fact_convert_to_tz(tz: str) -> Adjustment:
    """Returns adjustment function that converts all timestamps into timezone ``tz``."""

    def adjustment(s: pd.Series) -> pd.Series:
        return s.tz_convert(tz)

    return adjustment


convert_to_berlin: Adjustment = fact_convert_to_tz("Europe/Berlin")


def fact_fixed_to_float(fixed: str) -> Adjustment:
    """
    Use if: api returns series with frequency in incorrect (fixed) timezone.

    Parameters
    ----------
    fixed : str
        The timezone (UTC-offset) that the timestamps must be interpreted in.

    Returns
    -------
    Adjustment function

    Example
    -------
    The following timeseries has UTC timestamps but denote the start of a day in the CET
    timezone:

    2022-08-16 23:00:00+00:00      226.047
    2022-08-17 23:00:00+00:00      226.068

    The function ``ac = fact_fixed_to_float("+01:00")`` turns it into

    2022-08-17 00:00:00      226.047
    2022-08-18 00:00:00      226.068
    """

    def adjustment(s: pd.Series) -> pd.Series:
        return s.tz_convert(fixed).tz_localize(None)

    return adjustment


def fact_fixed_to_correct(fixed: str, correct: str) -> Adjustment:
    """
    Use if: api returns series with frequency in incorrect (fixed) timezone.

    Parameters
    ----------
    fixed : str
        The timezone (UTC-offset) that the timestamps must be interpreted in.
    correct : str
        The timezone that the timestamps must be converted to.

    Returns
    -------
    Adjustment function

    Example
    -------
    The following timeseries has UTC timestamps but denote the start of a day in the CET
    timezone:

    2022-08-16 23:00:00+00:00      226.047
    2022-08-17 23:00:00+00:00      226.068

    The function ``ac = fact_fixed_to_correct("+01:00", "Europe/Berlin")`` turns it into

    2022-08-17 00:00:00+02:00      226.047
    2022-08-18 00:00:00+02:00      226.068
    """

    def adjustment(s: pd.Series) -> pd.Series:
        return (
            s.tz_convert(fixed)
            .tz_localize(None)
            .tz_localize(correct, ambiguous="infer")
        )

    return adjustment


cet_to_float: Adjustment = fact_fixed_to_float("+01:00")
cet_to_berlin: Adjustment = fact_fixed_to_correct("+01:00", "Europe/Berlin")


def fact_frequency(freq: str) -> Adjustment:
    """Returns an adjustment function that infers the frequency and sets it to ``freq`` if none
    can be inferred."""

    def adjustment(s: pd.Series) -> pd.Series:
        return pf.tools.freq.set_to_frame(s, freq)

    return adjustment


hourly_frequency: Adjustment = fact_frequency("H")
quarterhourly_frequency: Adjustment = fact_frequency("15T")
daily_frequency: Adjustment = fact_frequency("D")
infer_frequency: Adjustment = fact_frequency(None)


def makeleft(s: pd.Series) -> pd.Series:
    """Assume rightbound (and turn into into leftbound) if series have <= 2h gap between
    first two timestamps."""
    td = s.index[1] - s.index[0]
    if td <= dt.timedelta(hours=2):
        s.index = pf.tools.righttoleft.index(s.index)
    return s


# def standardize_belvis(tz) -> Adjustment:
#     def adjustment(s: pd.Series, *args) -> pd.Series:
#         td = s.index[1] - s.index[0]
#         if td <= dt.timedelta(hours=2):
#             bound = "right"
#         else:
#             bound = "left"
#         return pf.standardize(s, "aware", bound, tz=tz, floating=False)

#     return adjustment
