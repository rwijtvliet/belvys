import datetime as dt
from collections import defaultdict
from typing import Dict, Iterable, Union

import pandas as pd
import portfolyo as pf

from . import adjustment
from .adjustment import Adjustment
from .api import Api
from .common import print_status
from .structure import Structure, Ts, TsTree


def fact_default_aftercare(tz) -> Adjustment:

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

    If .portfolio_pfl() and .price_pfl() raise an Exception when creating the ``PfLine``
    instance, inspect the series that the PfLine receives as input, by setting their
    ``debug`` parameter to True.
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
    def aftercare(self) -> Adjustment:
        return self._aftercare

    @aftercare.setter
    def aftercare(self, aftercare: Adjustment) -> None:
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
            print_status(f"{ts.pfid} | {ts.tsid} | {ts.name} | [{ts_left}-{ts_right}]")
            ts.series = self.api.series(ts.tsid, ts_left, ts_right, **kwargs)
        if isinstance(ts_tree, Dict):
            for subtree in ts_tree.values():
                self._fetch_series(subtree, ts_left, ts_right, **kwargs)
        elif isinstance(ts_tree, Iterable):  # Must be after Dict
            for branch in ts_tree:
                self._fetch_series(branch, ts_left, ts_right, **kwargs)

    def _pfline(self, ts_tree: TsTree) -> pf.PfLine:
        """Create a portfolio line from the data stored in the ts_tree series."""

        # MultiPfLine.

        if isinstance(ts_tree, Dict):
            children = {}
            for name, subtree in ts_tree.items():
                children[name] = self._pfline(subtree)
            return pf.PfLine(children)

        # SinglePfLine.

        tss = [ts_tree] if isinstance(ts_tree, Ts) else ts_tree
        # Collect the timeseries values from Belvis.
        series_by_dimension = defaultdict(list)
        for ts in tss:
            s = ts.series  # series as returned by api.
            # Here we make corrections for design decisions in our Belvis database.
            if self.aftercare is not None:
                s = self.aftercare(s, ts.tsid, ts.pfid, ts.name)
            # Sort by dimensionality.
            dim = s.pint.dimensionality
            series_by_dimension[dim].append(s)
        # Sum to get one series per dimension.
        data = [sum(s) for s in series_by_dimension.values()]
        # Turn into portfolio line at wanted frequency.
        pfl = pf.PfLine(data)
        return pfl.asfreq(self.structure.freq)

    def general_pfl(
        self,
        pfid: str,
        tsname: str,
        ts_left: Union[str, pd.Timestamp, dt.datetime] = None,
        ts_right: Union[str, pd.Timestamp, dt.datetime] = None,
        missing2zero: bool = True,
        debug: bool = False,
    ) -> pf.PfLine:
        """Retrieve a portfolio line with portfolio-specific volume and/or price data
        from Belvis, without using the structure Use if wanted timeseries is not specified in the structure file.

        Parameters
        ----------
        pfid : str
            Id of portfolio as found in Belvis. Must be original.
        tsname : str
            Name of the timeseries. Must be exact.
        ts_left : Union[str, pd.Timestamp, dt.datetime], optional
        ts_right : Union[str, pd.Timestamp, dt.datetime], optional
            Start and end of delivery period. If both omitted, uses the front year. If
            one omitted, uses the start of the (same or following) year.
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        debug : bool, optional (default: False)
            If True, stops after fetching timeseries data from api; before applying the
            aftercare functions.

        Returns
        -------
        pf.PfLine
        """
        # Fix timestamps.
        ts_left, ts_right = pf.tools.leftandright.stamps(ts_left, ts_right)
        # Get ts tree and fetch data.
        ts_tree = Ts(pfid, tsname)
        self.api.series(ts_tree, ts_left, ts_right, missing2zero=missing2zero)
        if debug:
            return ts_tree
        # Turn into portfolio line.
        return self._pfline(ts_tree)

    def portfolio_pfl(
        self,
        pfid: str,
        pflineid: str,
        ts_left: Union[str, pd.Timestamp, dt.datetime] = None,
        ts_right: Union[str, pd.Timestamp, dt.datetime] = None,
        missing2zero: bool = True,
        *,
        debug: bool = False,
    ) -> pf.PfLine:
        """Retrieve a portfolio line with portfolio-specific volume and/or price data
        from Belvis.

        Parameters
        ----------
        pfid : str
            Id of portfolio as defined in .Structure. May be original or synthetic.
        pflineid : str
            Id of portfolio line as defined in .structure
        ts_left : Union[str, pd.Timestamp, dt.datetime], optional
        ts_right : Union[str, pd.Timestamp, dt.datetime], optional
            Start and end of delivery period. If both omitted, uses the front year. If
            one omitted, uses the start of the (same or following) year.
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        debug : bool, optional (default: False)
            If True, stops after fetching timeseries data from api; before applying the
            aftercare functions.

        Returns
        -------
        pf.PfLine
        """
        # Fix timestamps.
        ts_left, ts_right = pf.tools.leftandright.stamps(ts_left, ts_right)
        # Get ts trees and fetch data.
        ts_trees = []
        for pfid in self.structure.to_original_pfids(pfid):
            ts_tree = self.structure.tstree_pfline(pfid, pflineid)
            self._fetch_series(ts_tree, ts_left, ts_right, missing2zero=missing2zero)
            ts_trees.append(ts_tree)
        if debug:
            return ts_trees
        # Turn into portfolio line.
        pflines = []
        for ts_tree in ts_trees:
            pflines.append(self._pfline(ts_tree))
        return sum(pflines)

    def price_pfl(
        self,
        priceid: str,
        ts_left: Union[str, pd.Timestamp, dt.datetime] = None,
        ts_right: Union[str, pd.Timestamp, dt.datetime] = None,
        missing2zero: bool = True,
        *,
        debug: bool = False,
    ) -> pf.PfLine:
        """Retrieve a portfolio line with portfolio-UNspecific price data from Belvis.

        Parameters
        ----------
        priceid : str
            Id of price timeseries as defined in .structure
        ts_left : Union[str, pd.Timestamp, dt.datetime], optional
        ts_right : Union[str, pd.Timestamp, dt.datetime], optional
            Start and end of delivery period. If both omitted, uses the front year. If
            one omitted, uses the start of the (same or following) year.
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.

        Returns
        -------
        pf.PfLine
        """
        # Fix timestamps.
        ts_left, ts_right = pf.tools.leftandright.stamps(ts_left, ts_right)
        # Get ts trees and fetch data.
        ts_tree = self.structure.tstree_price(priceid)
        self._fetch_series(ts_tree, ts_left, ts_right, missing2zero=missing2zero)
        if debug:
            return ts_tree
        # Turn into portfolio line.
        return self._pfline(ts_tree)
