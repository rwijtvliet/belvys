from collections import defaultdict
from typing import Dict, Iterable, List, Union

import pandas as pd
import portfolyo as pf

from . import adjustment
from .adjustment import Aftercare
from .api import Api
from .common import print_status
from .structure import Structure, Ts, TsTree

SeriesTree = Union[pd.Series, Iterable[pd.Series], Dict[str, "SeriesTree"]]


def fact_default_aftercare(tz) -> Aftercare:
    convert_to_tz = adjustment.fact_convert_to_tz(tz)

    def aftercare(s: pd.Series, tsid: int, pfid: str, tsname: str) -> pd.Series:
        s = convert_to_tz(s)
        s = adjustment.infer_frequency(s)
        s = adjustment.makeleft(s)
        return s

    return aftercare


class Tenant:
    """Class to interact with belvis tenants and retrieve data.

    Notes
    -----
    An important attribute of this class is .aftercare, which is a function that is used
    to make small adjustments to the timeseries returned by the .api.series() method.
    This may be necessary due to local Belvis settings. The function must accept 4
    arguments: the pandas Series, the timeseries id, the portfolio id, and the timeseries
    name. It must return a pandas Series from which a portfolio line (portfolyo.PfLine)
    can be initialized.

    - By default, the function makes three adjustments: it sets the timezone (to the one
      specified in .structure.tz), it infers the frequency of the timeseries, and it makes
      the timestamps leftbound. (by assuming the timestamps returned by Belvis are
      leftbound if they represent daily (or longer) time periods, and rightbound
      otherwise.
    - If the default is not what is needed, the user must specify a custom aftercare
      function. If a specific timeseries needs a special treatment, the function parameters
      (the timeseries id, the pfid, the timeseries name) can be used in the function
      definition to target that timeseries only. If they are not needed, ``*args`` may
      be used to "eat up" the unneeded parameters.
    - There are several ready-made adjustment functions available in the ``belvys.adjustment``
      module.

    If .portfolio_pfl() and .price_pfl() raise an Exception when creating the ``PfLine``
    instance, inspect the series that the PfLine receives as input, by setting their
    ``output_series`` parameter to True.
    """

    def __init__(self, structure: Structure = None, api: Api = None):
        """
        Parameters
        ----------
        structure : Structure, optional
            The structure of the objects found in this tenant.
        api : Api, optional
            The connection to the rest api for this tenant.
        """
        self._structure = structure
        self._api = api
        self._aftercare = fact_default_aftercare(self.structure.tz)

    @property
    def structure(self) -> Structure:
        if self._structure is None:
            raise ValueError("No structure has been set yet. Set with .structure = ...")
        return self._structure

    @structure.setter
    def structure(self, structure: structure) -> None:
        self._structure = structure

    @property
    def api(self) -> Api:
        if self._api is None:
            raise ValueError("No API object has been set yet. Set with .api = ...")
        return self._api

    @api.setter
    def api(self, api: Api) -> None:
        self._api = api

    @property
    def aftercare(self) -> Aftercare:
        return self._aftercare

    @aftercare.setter
    def aftercare(self, aftercare: Aftercare) -> None:
        self._aftercare = aftercare

    # ---

    def update_cache(self) -> None:
        """Loop through all portfolios that may be fetched, find the timeseries they contain,
        and store all in cache. May take long time!
        """
        pfids_1 = self.structure.available_pfids(True)
        pfids_2 = [price["pfid"] for price in self.structure.prices.values()]
        for pfid in set([*pfids_1, *pfids_2]):
            _ = self.api.all_ts(pfid)

    def _fetch_series(self, ts_tree: TsTree, ts_left, ts_right, **kwargs) -> None:
        if isinstance(ts_tree, Ts):
            ts = ts_tree
            if ts.tsid is None:
                ts.tsid = self.api.find_tsid(ts.pfid, ts.name)
            print_status(f"{ts.tsid} | {ts.pfid} | {ts.name} | [{ts_left}-{ts_right}]")
            ts.series = self.api.series(ts.tsid, ts_left, ts_right, **kwargs)
        if isinstance(ts_tree, Dict):
            for subtree in ts_tree.values():
                self._fetch_series(subtree, ts_left, ts_right, **kwargs)
        elif isinstance(ts_tree, Iterable):  # Must be after Dict
            for branch in ts_tree:
                self._fetch_series(branch, ts_left, ts_right, **kwargs)

    def _pfline(self, series_tree: SeriesTree) -> pf.PfLine:
        """Create a portfolio line from the data stored in the series_tree."""

        # NestedPfLine.

        if isinstance(series_tree, Dict):
            children = {
                name: self._pfline(subtree) for name, subtree in series_tree.items()
            }

            # Turn all revenue-only pflines into complete pflines.
            children = {
                name: child | pf.Q_(0.0, "MW")
                if child.kind is pf.Kind.REVENUE
                else child
                for name, child in children.items()
            }
            return pf.PfLine(children)

            # TODO: use code below once portfolyo allows for NestedPfLine | 0 MW.
            kinds = set([child.kind for child in children.values()])
            if len(kinds) == 1:
                return pf.PfLine(children)

            def make_complete(pfl: pf.PfLine):
                if pfl.kind in (pf.Kind.REVENUE, pf.Kind.PRICE):
                    return pfl | pf.Q_(0, "MW")
                elif pfl.kind is pf.Kind.VOLUME:
                    return pfl | pf.Q_(0, "Eur/MWh")
                return pfl  # pfl.kind is pf.Kind.COMPLETE

            return pf.PfLine(
                {name: make_complete(child) for name, child in children.items()}
            )

        # FlatPfLine.

        pfl = pf.PfLine(series_tree)
        return pfl.asfreq(self.structure.freq)

        # tss = [ts_tree] if isinstance(ts_tree, Ts) else ts_tree
        # # Collect the timeseries values from Belvis.
        # series_by_dimension = defaultdict(list)
        # for ts in tss:
        #     s = ts.series  # series as returned by api.
        #     # Here we make corrections for design decisions in our Belvis database.
        #     if self.aftercare is not None:
        #         s = self.aftercare(s, ts.tsid, ts.pfid, ts.name)
        #     # Sort by dimensionality.
        #     dim = s.pint.dimensionality
        #     series_by_dimension[dim].append(s)
        # # Sum to get one series per dimension.
        # data = [sum(s) for s in series_by_dimension.values()]
        # # Turn into portfolio line at wanted frequency.
        # pfl = pf.PfLine(data)

    def general_pfl(
        self,
        pfid: str,
        tsname: str,
        ts_left: pd.Timestamp,
        ts_right: pd.Timestamp,
        missing2zero: bool = True,
        output_as_series: bool = False,
    ) -> pf.PfLine:
        """Retrieve a portfolio line with portfolio-specific volume and/or price data
        from Belvis, without using the structure Use if wanted timeseries is not specified in the structure file.

        Parameters
        ----------
        pfid : str
            Id of portfolio as found in Belvis. Must be original.
        tsname : str
            Name of the timeseries. Must be exact.
        ts_left : pd.Timestamp
            Start of delivery period (incl)
        ts_right : pd.Timestamp
            End of delivery period (excl)
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        output_as_series : bool, optional (default: False)
            If True, stops after fetching timeseries data from api, and return those as
            series, list of series, or nested dictionary.

        Returns
        -------
        pf.PfLine
        """
        # Get ts tree and fetch data.
        ts_tree = Ts(pfid, tsname)
        self._fetch_series(ts_tree, ts_left, ts_right, missing2zero=missing2zero)
        series_tree = to_series_tree(ts_tree, self.aftercare)
        if output_as_series:
            return series_tree
        # Turn into portfolio line.
        return self._pfline(series_tree)  # TODO

    def portfolio_pfl(
        self,
        pfid: str,
        pflineid: str,
        ts_left: pd.Timestamp,
        ts_right: pd.Timestamp,
        missing2zero: bool = True,
        *,
        output_as_series: bool = False,
    ) -> pf.PfLine:
        """Retrieve a portfolio line with portfolio-specific volume and/or price data
        from Belvis.

        Parameters
        ----------
        pfid : str
            Id of portfolio as defined in .Structure. May be original or synthetic.
        pflineid : str
            Id of portfolio line as defined in .structure
        ts_left : pd.Timestamp
            Start of delivery period (incl)
        ts_right : pd.Timestamp
            End of delivery period (excl)
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        output_as_series : bool, optional (default: False)
            If True, stops after fetching timeseries data from api, and return those as
            series, list of series, or nested dictionary.

        Returns
        -------
        pf.PfLine
        """
        # Get ts trees and fetch data.
        ts_trees = []
        for pfid in self.structure.to_original_pfids(pfid):
            ts_tree = self.structure.tstree_pfline(pfid, pflineid)
            self._fetch_series(ts_tree, ts_left, ts_right, missing2zero=missing2zero)
            ts_trees.append(ts_tree)
        # Turn into series.
        series_trees = [to_series_tree(ts_tree, self.aftercare) for ts_tree in ts_trees]
        if output_as_series:
            return series_trees
        # Turn into portfolio line.
        return sum([self._pfline(series_tree) for series_tree in series_trees], None)

    def price_pfl(
        self,
        priceid: str,
        ts_left: pd.Timestamp,
        ts_right: pd.Timestamp,
        missing2zero: bool = True,
        *,
        output_as_series: bool = False,
    ) -> pf.PfLine:
        """Retrieve a portfolio line with portfolio-UNspecific price data from Belvis.

        Parameters
        ----------
        priceid : str
            Id of price timeseries as defined in .structure
        ts_left : pd.Timestamp
            Start of delivery period (incl)
        ts_right : pd.Timestamp
            End of delivery period (excl)
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        output_as_series : bool, optional (default: False)
            If True, stops after fetching timeseries data from api, and return those as
            series, list of series, or nested dictionary.

        Returns
        -------
        pf.PfLine
        """
        # Get ts trees and fetch data.
        ts_tree = self.structure.tstree_price(priceid)
        self._fetch_series(ts_tree, ts_left, ts_right, missing2zero=missing2zero)
        series_tree = to_series_tree(ts_tree, self.aftercare)
        if output_as_series:
            return series_tree
        # Turn into portfolio line.
        return self._pfline(series_tree)


def to_series_tree(ts_tree: TsTree, aftercare: Aftercare) -> SeriesTree:
    """Apply aftercare function and sum by dimension."""
    # NestedPfLine.

    if isinstance(ts_tree, Dict):  # nested
        ts_dict = ts_tree
        return {
            name: to_series_tree(subtree, aftercare)
            for name, subtree in ts_dict.items()
        }

    # FlatPfLine.

    elif isinstance(ts_tree, Ts):  # one series
        ts = ts_tree
        return apply_aftercare(ts, aftercare)

    else:  # list of series
        tss = ts_tree
        return sum_same_dimensionality([apply_aftercare(ts, aftercare) for ts in tss])


def apply_aftercare(ts: Ts, aftercare: Aftercare) -> pd.Series:
    if aftercare:
        return aftercare(ts.series, ts.tsid, ts.pfid, ts.name)
    else:
        return ts.series


def sum_same_dimensionality(series: Iterable[pd.Series]) -> List[pd.Series]:
    """Condense a collection of series by summing the ones with the same pint unit.
    The series in the returned list all have a different dimensionality."""
    series_by_dimension = defaultdict(list)
    for s in series:
        # Sort by dimensionality.
        dim = s.pint.dimensionality
        series_by_dimension[dim].append(s)
    # Sum to get one series per dimension.
    return [sum(s) for s in series_by_dimension.values()]
