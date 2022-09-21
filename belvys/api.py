"""Get data from Belvis rest api."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import urllib
from dataclasses import dataclass
from typing import Callable, Dict, List, Union

import numpy as np
import pandas as pd
import requests
import yaml

from .common import print_status


def create_url(server: str, path: str, *queryparts: str) -> str:
    """Convenience function to build URL for querying a server."""
    sp = f"{server}{path}"
    query = "&".join([urllib.parse.quote(qp, safe=":=") for qp in queryparts])
    url = sp if not query else f"{sp}?{query}"
    return url


@dataclass
class Access:
    # Zero-parameter function to authorize with server.
    authenticate: Callable[[]]
    # Function used to fetch data from the server.
    request: Callable[[str], requests.request]

    def __post_init__(self):
        self.authenticate()  # Run once to verify authentication works.

    @classmethod
    def from_usr_pwd(cls, server: str, tenant: str, usr: str, pwd: str) -> Access:
        """Use username and password to access Belvis API.

        Parameters
        ----------
        server : str
            Address of Belvis server, incl port.
        tenant : str
            Name of Belvis tenant.
        usr : str
            Username.
        pwd : str
            Password.
        """
        session = requests.Session()
        auth_url = create_url(
            server, "/rest/session", f"tenant={tenant}", f"usr={usr}", f"pwd={pwd}"
        )

        def auth() -> None:
            response = session.get(auth_url)
            if response.status_code != 200:
                raise PermissionError(
                    f"Please check authentication details: {response}"
                )

        def req(url: str) -> requests.request:
            return session.get(url)

        return cls(auth, req)


class Api:
    """A class to interact with a Belvis Rest API server."""

    @classmethod
    def from_file(cls, filepath: Union[str, pathlib.Path]) -> Api:
        """Load api data from file.

        Parameters
        ----------
        filepath : Union[str, pathlib.Path]
            Path to load yaml api configuration from. Also the path to save api configuration
            (which includes the cache).

        Notes
        -----
        The api configuration file must have the keys 'server' (= string of server address
        including port), 'tenant' (= name of the belvis tenant), and possibly 'cache'
        (= dictionary).
        """
        api_yml = yaml.load(open(filepath), Loader=yaml.FullLoader)
        return cls(**api_yml, filepath=filepath)

    def __init__(
        self,
        server: str,
        tenant: str,
        cache: Dict[str, Dict[str, int]] = None,
        filepath: pathlib.Path = None,
    ) -> None:
        """
        Parameters
        ----------
        server : str
            Server address including port.
        tenant : str
            Name of the Belvis tenant.
        cache : Dict[str, Dict[str, int]], optional
            Cache to use for lookup. Nested dictionany with format {pfid: {tsname: tsid}}
        filepath : pathlib.Path, optional
            If specified, saves api data (server, tenant, cache) to this file after every
            change for persistent storage. If not specified, the data is cached only for
            the duration of the class instance.
        """
        self._retry = True
        self._server = server
        self._tenant = tenant
        self._cache = cache if cache is not None else {}
        self._filepath = filepath
        # Must be set later.
        self._access: Access = None

    server: str = property(lambda self: self._server)
    tenant: str = property(lambda self: self._tenant)
    cache: Dict = property(lambda self: self._cache)
    filepath: pathlib.Path = property(lambda self: self._filepath)

    @filepath.setter
    def filepath(self, path: pathlib.Path):
        self._filepath = path

    @property
    def access(self) -> Access:
        if self._access is None:
            raise ValueError(
                "No access method has been set yet. Set with .access_from_usr_pwd()."
            )
        return self._access

    # ---

    def access_from_usr_pwd(self, usr: str, pwd: str) -> None:
        """Specify username and password to access Belvis API.

        Parameters
        ----------
        usr : str
            Username.
        pwd : str
            Password.
        """
        self._access = Access.from_usr_pwd(self.server, self.tenant, usr, pwd)

    def to_file(self, filepath: pathlib.Path) -> None:
        """Write api configuration to file. Access method is not stored.

        Parameters
        ----------
        filepath : pathlib.Path
            Path of file to store data to.
        """
        yaml.dump(
            {"server": self.server, "tenant": self.tenant, "cache": self.cache},
            open(filepath, "w"),
            allow_unicode=True,
            sort_keys=False,
        )

    def read_cache(self, pfid: str, tsname: str) -> int:
        """Retrieve belvis timeseries id from cache file. Returns None if not found.
        Case sensitive.

        Parameters
        ----------
        pfid : str
            Id (= short name) of portfolio.
        tsname : str
            Name of timeseries.

        Returns
        -------
        int
        """
        return self.cache.get(pfid, {}).get(tsname)

    def write_cache(self, pfid: str, tsname_to_tsid: Dict[str, int]) -> None:
        """Write belvis timeseries id into cache file. Overwrites if already present.

        Parameters
        ----------
        pfid : str
            Id (= short name) of the Belvis portfolio.
        tsname_to_tsid : Dict[str, int]
            Dictionary mapping timeseries names to their ids.
        """
        # Insert new data.
        if pfid not in self.cache:
            self.cache[pfid] = {}
        self.cache[pfid].update(tsname_to_tsid)
        # Save file.
        if self.filepath is not None:
            self.to_file(self.filepath)

    def query(self, url: str) -> Union[Dict, List]:
        """Query connection for general information."""
        try:
            response = self.access.request(url)

        except ConnectionError as e:
            raise ConnectionError("Check connection to server.") from e

        if response.status_code == 200:
            # Success.
            self._retry = True
            return json.loads(response.text)
        elif self._retry is True:
            # Authentication might have expired, or maybe has never been done before. Try once.
            self._retry = False
            self.access.authenticate()
            return self.query(url)  # retry.
        else:
            raise RuntimeError(response)

    def metadata(self, tsid: int) -> Dict:
        """Get information about timeseries.

        Parameters
        ----------
        tsid : int
            Belvis id of timeseries.

        Returns
        -------
        dict
            Metadata about the timeseries.
        """
        url = create_url(
            self.server, f"/rest/energy/belvis/{self.tenant}/timeSeries/{tsid}"
        )
        return self.query(url)

    def all_ts(self, pfid: str) -> Dict[str, int]:
        """Use API to find all timeseries in a Belvis portfolio and store in cache. May
        take a long time if portfolio has many timeseries.

        Parameters
        ----------
        pfid : str
            Id (= short name) of Belvis portfolio.

        Returns
        -------
        Dict[str, int]
            Dictionary with found timeseries. Keys are the timeseries names, the values are
            the timeseries ids.
        """
        # Get all timeseries ids in the portfolio.
        url = create_url(
            self.server,
            f"/rest/energy/belvis/{self.tenant}/timeSeries",
            f"instancetoken={pfid}",
        )
        paths = self.query(url)
        tsids = [int(path.split("/")[-1]) for path in paths]

        # Get name of each timeseries id.
        found = {}
        for tsid in tsids:
            info = self.metadata(tsid)
            tsid, tsname = int(info["id"]), info["timeSeriesName"]
            found[tsname] = tsid

        # Save ALL that are found to cache.
        self.write_cache(pfid, found)
        return found

    def find_tsids(
        self,
        pfid: str,
        tsname: str = "",
        case_insensitive: bool = False,
        allow_partial: bool = False,
    ) -> Dict[str, int]:
        """Use API to find specific timeseries in a Belvis portfolio. May take a long
        time if portfolio has many timeseries.

        Parameters
        ----------
        pfid : str
            Id (= short name) of Belvis portfolio.
        tsname : str, optional (default: return all timeseries).
            Name of timeseries.
        case_insensitive : bool, optional (default: False)
            If True, do a case insensitive search for the timeseries name.
        allow_partial : bool, optional (default: False)
            If True, also returns timeseries if the name partially matches.

        Returns
        -------
        Dict[str, int]
            Dictionary with found timeseries. Keys are the timeseries names, the values are
            the timeseries ids.
        """
        if case_insensitive:
            tsname = tsname.lower()

        def matchingname(found: str) -> bool:
            if case_insensitive:
                found = found.lower()
            return tsname in found if allow_partial else tsname == found

        # Filter on timeseries name.
        all_ts = self.all_ts(pfid)
        return {tsname: tsid for tsname, tsid in all_ts.items() if matchingname(tsname)}

    def find_tsid(self, pfid: str, tsname: str) -> int:
        """Find Belvis id number of timeseries.

        Parameters
        ----------
        pfid : str
            Id (=short name) of portfolio as found in Belvis.
        tsname : str
            Full name of timeseries.

        Returns
        -------
        int
            id of found timeseries.
        """
        # Try to get from cache first.
        if (tsid := self.read_cache(pfid, tsname)) is not None:
            return tsid

        # No cached value found: get from API.
        print_status(
            f"Timeseries '{tsname}' in portfolio '{pfid}' not found. If cache is complete and"
            " up to date, this should not happen, and ``pfid`` or ``tsname`` may be incorrect."
        )
        hits = self.find_tsids(pfid, tsname)
        # Raise error if 0 or > 1 found.
        if len(hits) == 0:
            raise ValueError(
                f"No timeseries with exact name '{tsname}' found in portfolio '{pfid}'."
                " Check if ``pfid`` and ``tsname`` are correct."
            )
        elif len(hits) > 1:
            raise ValueError(
                f"Multiple timeseries with exact name '{tsname}' found in portfolio '{pfid}'."
                " Check your Belvis instance."
            )
        return next(iter(hits.values()))

    def series(
        self,
        tsid: int,
        ts_left: Union[pd.Timestamp, dt.datetime],
        ts_right: Union[pd.Timestamp, dt.datetime],
        *,
        leftrange: str = "exclusive",
        rightrange: str = "inclusive",
        missing2zero: bool = True,
        blocking: bool = True,
    ) -> pd.Series:
        """Return timeseries in given delivery time interval using its id.

        Parameters
        ----------
        tsid : int
            Belvis id of timeseries.
        ts_left : Union[pd.Timestamp, dt.datetime]
        ts_right : Union[pd.Timestamp, dt.datetime]
        leftrange : str, optional (default: 'exclusive')
            'inclusive' ('exclusive') to get values with timestamp that is >= (>) ts_left.
            Default: 'exclusive' because timestamps in Belvis are *usually* right-bound.
        rightrange : str, optional (default: 'inclusive')
            'inclusive' ('exclusive') to get values with timestamp that is <= (<) ts_right.
            Default: 'inclusive' because timestamps in Belvis are *usually* right-bound.
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        blocking : bool, optional (default: True)
            If True, recalculates data that is not up-to-date before returning; might take
            long time or result in internal-server-error. If False, return most up-to-date
            data that is available without recalculating.

        Returns
        -------
        pd.Series
            with resulting information.

        Notes
        -----
        Returns series with data as found in Belvis; no correction (e.g. for right-bounded
        timestamps) done.
        """
        # Get metadata and print status message.
        metadata = self.metadata(tsid)
        # Get data.
        url = create_url(
            self.server,
            f"/rest/energy/belvis/{self.tenant}/timeSeries/{tsid}/values",
            f"timeRange={ts_left.isoformat()}--{ts_right.isoformat()}",
            f"timeRangeType={leftrange}-{rightrange}",
            f"blocking={str(blocking).lower()}",
        )
        records = self.query(url)
        df = pd.DataFrame.from_records(records)
        # Replace missing values.
        mask = df["pf"] == "missing"
        df.loc[mask, "v"] = 0 if missing2zero else np.nan
        # Find unit.
        unit = metadata["measurementUnit"]
        # Turn into series.
        s = pd.Series(df["v"].to_list(), pd.DatetimeIndex(df["ts"]), f"pint[{unit}]")
        s.index.freq = pd.infer_freq(s.index)
        return s

    def series_from_tsname(
        self,
        pfid: str,
        tsname: str,
        ts_left: Union[pd.Timestamp, dt.datetime],
        ts_right: Union[pd.Timestamp, dt.datetime],
        *,
        leftrange: str = "exclusive",
        rightrange: str = "inclusive",
        missing2zero: bool = True,
        blocking: bool = True,
    ) -> pd.Series:
        """Return timeseries in given delivery time interval, using its name and portfolio
        id.

        Parameters
        ----------
        pfid : int
            ID (=short name) of portfolio in Belvis.
        tsname : str
            Name of the timeseries. Must be exact.
        ts_left : Union[pd.Timestamp, dt.datetime]
        ts_right : Union[pd.Timestamp, dt.datetime]
        leftrange : str, optional (default: 'exclusive')
            'inclusive' ('exclusive') to get values with timestamp that is >= (>) ts_left.
            Default: 'exclusive' because timestamps in Belvis are *usually* right-bound.
        rightrange : str, optional (default: 'inclusive')
            'inclusive' ('exclusive') to get values with timestamp that is <= (<) ts_right.
            Default: 'inclusive' because timestamps in Belvis are *usually* right-bound.
        missing2zero : bool, optional (default: True)
            What to do with values that are flagged as 'missing'. True to replace with 0,
            False to replace with nan.
        blocking : bool, optional (default: True)
            If True, recalculates data that is not up-to-date before returning; might take
            long time or result in internal-server-error. If False, return most up-to-date
            data that is available without recalculating.

        Returns
        -------
        pd.Series
            with resulting information.

        Notes
        -----
        - Returns series with data as found in Belvis; no correction (e.g. for right-bounded
          timestamps) done.
        - If not yet cached, the ``.series()`` method is potentially a lot faster.
        """
        tsid = self.find_tsid(pfid, tsname)
        return self.series(
            tsid,
            ts_left,
            ts_right,
            leftrange=leftrange,
            rightrange=rightrange,
            missing2zero=missing2zero,
            blocking=blocking,
        )
