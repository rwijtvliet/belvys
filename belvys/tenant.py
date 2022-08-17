import datetime as dt
from collections import defaultdict
from typing import Callable, Dict, Iterable, Union

import pandas as pd
import portfolyo as pf

from . import aftercarestore
from .aftercarestore import Aftercare
from .api import Api
from .structure import Structure, TsIdTree, TsNameTree


class Tenant:
    """Class to interact with belvis tenants.

    Notes
    -----
    An important attribute of this class is .aftercare, which is a list of functions.
    These functions are used to make small changes to the timeseries returned by the
    .api.series() method. This may be necessary due to local Belvis settings. Each
    function must accept a pandas Series and an int (the timeseries id) and return a
    pandas Series.
    - By default, the list contains a single function, which brings the series in
      standardized form, by assuming the timestamps returned by Belvis are leftbound if
      they represent daily (or longer) time periods, and rightbound otherwise. It is a
      curried version of portfolyo.standardize which also sets the timezone.
    - The functions are called in order; the end result should be timeseries from which
      a portfolio line (portfolyo.PfLine) can be initialized.
    - If a specific timeseries needs a special treatment, the second function parameter
      (the timeseries id) can be used in the function code to target that timeseries only.
    - A function can be prepended to the existing list with .prepend_aftercare(), appended
      to it with .append_aftercare(), or the whole list can be set with .aftercare = [...].

    If .portfolio_pfl() and .price_pfl() raise an Exception when creating the ``PfLine``
    instance, inspect the series that the PfLine receives as input, with the
    .portfolio_series() and .price_series() functions.
    """

    def __init__(
        self,
        structure: Structure = None,
        api: Api = None,
    ):
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
        self._aftercare = [aftercarestore.standardize_belvis(self.structure.tz)]

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
    def aftercare(self) -> Iterable[Aftercare]:
        return self._aftercare

    @aftercare.setter
    def aftercare(self, aftercare_fns: Iterable[Aftercare] = None) -> None:
        if aftercare_fns is None:
            self._aftercare = []
        elif isinstance(aftercare_fns, Callable):
            self._aftercare = [aftercare_fns]
        else:
            self._aftercare = aftercare_fns

    def prepend_aftercare(self, aftercare_fn: Aftercare) -> None:
        """Prepend function to list of aftercare functions."""
        if not isinstance(aftercare_fn, Callable):
            raise TypeError("Must provide a function.")
        self._aftercare = [aftercare_fn, *self._aftercare]

    def append_aftercare(self, aftercare_fn: Aftercare) -> None:
        """Append function to list of aftercare functions."""
        if not isinstance(aftercare_fn, Callable):
            raise TypeError("Must provide a function.")
        self._aftercare.append(aftercare_fn)

    # ---

    def update_cache(self) -> None:
        """Loop through all portfolios that may be fetched, find the timeseries they contain,
        and store all in cache. May take long time!
        """
        pfids_1 = self.structure.available_pfids(True)
        pfids_2 = [price["pfid"] for price in self.structure.prices.values()]
        for pfid in set([*pfids_1, *pfids_2]):
            _ = self.api.all_ts(pfid)

    def _tsnames_to_tsid_tree(self, pfid: str, tsname_tree: TsNameTree) -> TsIdTree:
        """Create tree of Belvis timeseries ids (representing a flat or nested PfLine).

        Parameters
        ----------
        pfid : str
            id (= short name) of the portfolio as found in Belvis.
        tsname_tree : TsNameTree
            One or more timeseries names (string or Iterable of strings), or dictionary
            with as keys the children names and as values the timeseries names (or again
            a dictionary).

        Returns
        -------
        TsIdTree
            Same tree structure as ``tsname_tree``, but with each timeseries name replaced
            by its Belvis timeseries id.
        """
        if isinstance(tsname_tree, Dict):
            return {
                k: self._tsnames_to_tsid_tree(pfid, ts) for k, ts in tsname_tree.items()
            }
        elif isinstance(tsname_tree, str):
            return self.api.find_tsid(pfid, tsname_tree)
        elif isinstance(tsname_tree, Iterable):  # str and Dict also Iterable
            return [self._tsnames_to_tsid_tree(pfid, ts) for ts in tsname_tree]
        raise TypeError(
            f"Expected ``tsname_tree`` to be string, dictionary, or iterable; got {type(tsname_tree)}."
        )

    def _tsid_trees_pfline(self, pfid: str, pflineid: str) -> Iterable[TsIdTree]:
        """Tree of timeseries Id's for wanted portfolio line.

        Parameters
        ----------
        pfid : str
            Id of portfolio. May be original or synthetic.
        pflineid : str
            Id of the portfolio line.

        Returns
        -------
        Iterable[TsIdTree]
            List of timeseries id trees.
        """
        tsid_trees = []
        for pfid in self.structure.to_original_pfids(pfid):
            tsname_tree = self.structure.tsname_tree(pfid, pflineid)
            tsid_tree = self._tsnames_to_tsid_tree(pfid, tsname_tree)
            tsid_trees.append(tsid_tree)
        return tsid_trees

    def _tsid_tree_price(self, priceid: str) -> TsIdTree:
        """Tree of timeseries Id's for wanted price.

        Parameters
        ----------
        priceid : str
            Id of price.

        Returns
        -------
        TsIdTree
            Timeseries id tree.
        """
        price = self.structure.prices.get(priceid)
        if price is None:
            raise ValueError(f"The price ({priceid}) does not exists for this tenant.")
        tsid_tree = self._tsnames_to_tsid_tree(price["pfid"], price["tsnames"])
        return tsid_tree

    def _pfline(self, tsid_tree: TsIdTree, ts_left, ts_right, **kwargs) -> pf.PfLine:
        """Get data and put into portfolio line object.

        Parameters
        ----------
        tsid_tree : RecursiveIntListDict
            Ids of timeseries in belvis.
        ts_left : str | pandas.Timestamp | dt.datetime
        ts_right : str | pandas.Timestamp | dt.datetime
        Additional **kwargs are passed onto the .api.series() method.

        Returns
        -------
        pf.PfLine
        """
        # MultiPfLine.

        if isinstance(tsid_tree, Dict):
            children = {}
            for name, subtree in tsid_tree.items():
                children[name] = self._pfline(subtree, ts_left, ts_right, **kwargs)
            return pf.PfLine(children)

        # SinglePfLine.

        tsids = [tsid_tree] if isinstance(tsid_tree, int) else tsid_tree
        # Collect the timeseries values from Belvis.
        series_by_dimension = defaultdict(list)
        for tsid in tsids:
            s = self.api.series(tsid, ts_left, ts_right, **kwargs)
            # Here we make corrections for design decisions in our Belvis database.
            for fn in self.aftercare:
                s = fn(s, tsid)
            # Sort by dimensionality.
            dim = s.pint.dimensionality
            series_by_dimension[dim].append(s)
        # Sum to get one series per dimension.
        series = [sum(s) for s in series_by_dimension.values()]
        # Turn into portfolio line at wanted frequency.
        pfl = pf.PfLine(series)
        return pfl.asfreq(self.structure.freq)

    def portfolio_pfl(
        self,
        pfid: str,
        pflineid: str,
        ts_left: Union[str, pd.Timestamp, dt.datetime] = None,
        ts_right: Union[str, pd.Timestamp, dt.datetime] = None,
        missing2zero: bool = True,
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

        Returns
        -------
        pf.PfLine
        """
        # Fix timestamps.
        ts_left, ts_right = pf.ts_leftright(ts_left, ts_right)
        # Get tsids.
        tsid_trees = self._tsid_trees_pfline(pfid, pflineid)
        # Get data.
        pflines = []
        for tsid_tree in tsid_trees:
            pflines.append(
                self._pfline(tsid_tree, ts_left, ts_right, missing2zero=missing2zero)
            )
        return sum(pflines)

    def price_pfl(
        self,
        priceid: str,
        ts_left: Union[str, pd.Timestamp, dt.datetime] = None,
        ts_right: Union[str, pd.Timestamp, dt.datetime] = None,
        missing2zero: bool = True,
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
        ts_left, ts_right = pf.ts_leftright(ts_left, ts_right)
        # Get tsids.
        tsid_tree = self._tsid_tree_price(priceid)
        # Get data.
        return self._pfline(tsid_tree, ts_left, ts_right, missing2zero=missing2zero)
