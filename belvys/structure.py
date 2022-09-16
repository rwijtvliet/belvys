from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Union

import pandas as pd
import yaml

TsNameTree = Union[str, Iterable[str], Dict[str, "TsNameTree"]]


@dataclass
class Ts:
    pfid: str
    name: str
    tsid: int = None
    series: pd.Series = None


TsTree = Union[Ts, Iterable[Ts], Dict[str, "TsTree"]]


def create_tstree(pfid: str, tsname_tree: TsNameTree) -> TsTree:
    if isinstance(tsname_tree, Dict):
        return {k: create_tstree(pfid, subtree) for k, subtree in tsname_tree.items()}
    elif isinstance(tsname_tree, str):
        tsname = tsname_tree
        return [Ts(pfid, tsname)]
    elif isinstance(tsname_tree, Iterable):
        tsnames = tsname_tree
        return [Ts(pfid, tsname) for tsname in tsnames]


@dataclass
class Portfolios:
    original: Iterable[str]
    synthetic: Dict[str, Union[str, Iterable[str]]] = field(default_factory=dict)

    def __post_init__(self):
        # Assert that the class doesn't have missing refences.
        if not isinstance(self.original, Iterable):
            raise TypeError(f"'original' must be Iterable, got {type(self.original)}.")
        if not len(self.original):
            raise ValueError("'original' must have at least one element.")
        for ref in self.synthetic.values():
            try:
                self._assert_valid_ref(ref)
            except AssertionError as e:
                raise ValueError("Unexpected value for 'synthetic'") from e

    def _assert_valid_ref(self, ref: str) -> None:
        if isinstance(ref, str):
            assert ref in self.original or ref in self.synthetic.keys()
        elif isinstance(ref, Iterable):
            for r in ref:
                self._assert_valid_ref(r)
        else:
            raise AssertionError(
                f"Incorrect type for ``ref``: expected str or Iterable; got {type(ref)}."
            )


@dataclass
class Structure:
    """Structure of the belvis database; which portfolios and timeseries are of interest.

    Parameters
    ----------
    freq : str
        Frequency of the spot market, which is also the shortest frequency that is of
        interest, e.g. quarterhourly ('15T') for power and daily ('D') for gas. Ideally,
        all data in the Belvis database is available at this frequency.
    tz : str
        The timezone of the spot market and the Belvis database. It is the timezone that
        the data is converted into.
    pfline : Dict[str, TsNameTree]
        The portfolio lines that we are interested in.
        Dictionary with string keys (=pfline ids), which map onto the following possible
        values:

        - string value or list of string values (=timeseries name(s) as found in Belvis),
          which define a flat portfolio line (i.e., without children).
        - dictionary, which defines a mapping of child names onto timeseries name(s). May
          be nested.

    portfolios : Portfolios
        The portfolios we are interested in.
        Dictionary with at least the key 'original' which maps onto a list of strings (=
        the ids (=short names) of portfolios as found in Belvis). May also have a key
        'synthetic' which maps onto a dictionary, of which the keys are user-defined
        portfolio ids and the values are the original pfids that must be added.
    prices : Dict[str, Dict[str, Any]]
        The prices we are interested in.
        Dictionary with string keys (=price ids), which map onto a dictionary that has
        the keys 'pfid' (which has the id of the portfolio as its value) and 'tsnames'
        (which has a (list of) timeseries names as its value).
    corrections : Dict[str, Dict[str, Union[TsNameTree, None]]]
        If not all pflines can be found in all portfolios, we can specify this here.

        - If a portfolio has a pfline that is not found in the others (and therefore not
          specified in parameter ``pfline`` above), we can add a nested dictionary
          {pfid: {pflineid: tsnames}}.
        - If a porfolio does not have a pfline that is found in the others (and therefore
          specified in parameter ``pfline`` above), we can exclude it by adding the
          nested dictionary {pfid: {pflineid: None}}.

    Notes
    -----
    May be loaded from yaml file with the .from_file() class method.
    """

    freq: str
    tz: str
    pflines: Dict[str, TsNameTree]
    portfolios: Portfolios
    prices: Dict[str, Dict[str, Any]]
    corrections: Dict[str, Dict[str, Union[TsNameTree, None]]] = field(
        default_factory=dict
    )

    def _expand_tree(self, tsname_tree: TsNameTree) -> TsNameTree:
        """Check if tree refers to existing value, and replace if yes."""
        if tsname_tree is None:
            return tsname_tree
        elif isinstance(tsname_tree, Dict):
            return {k: self._expand_tree(ts) for k, ts in tsname_tree.items()}
        elif isinstance(tsname_tree, str):
            if tsname_tree in self.pflines:
                return self._expand_tree(self.pflines[tsname_tree])
            else:
                return tsname_tree
        else:
            return [self._expand_tree(ts) for ts in tsname_tree]

    def __post_init__(self):
        # Finish initialisation.
        self.portfolios = Portfolios(**self.portfolios)

        # Ensure pflines part is correct.
        self.pflines = {
            pflineid: self._expand_tree(tsname_tree)
            for pflineid, tsname_tree in self.pflines.items()
        }

        # Assert corrections part is valid.
        for pfid, pflinesdict in self.corrections.items():
            assert pfid in self.portfolios.original  # must override existing portfolio
            for pfline, ref in pflinesdict.items():
                if ref is None:
                    assert pfline in self.pflines.keys()

        # Assert prices part is valid.
        for pricedict in self.prices.values():
            assert "pfid" in pricedict
            assert "tsnames" in pricedict
            assert (
                isinstance(pricedict["tsnames"], str)
                or isinstance(pricedict["tsnames"], Dict)
                or isinstance(pricedict["tsnames"], Iterable)
            )

    @classmethod
    def from_file(cls, filepath: Union[str, pathlib.Path]) -> Structure:
        """Load structure from file.

        Parameters
        ----------
        filepath : Union[str, pathlib.Path]
            Path to load yaml structure file from.
        """
        conf_yml = yaml.load(open(filepath), Loader=yaml.FullLoader)
        return cls(**conf_yml)

    def tstree_pfline(self, pfid: str, pflineid: str) -> TsTree:
        """Timeseries that must be fetched to get the wanted pflineid for a given pfid.

        Parameters
        ----------
        pfid : str
            Id of portfolio. Must be original.
        pflineid : str
            Id of portfolio line.

        Returns
        -------
        TsTree
            Names of timeseries that must be fetched.
        """
        if pfid not in (avail := self.available_pfids(True)):
            raise ValueError(f"``pfid`` must one of {', '.join(avail)}.")

        # Use correction, if it exists.
        tsname_tree = self.corrections.get(pfid, {}).get(pflineid, "notfound")
        if tsname_tree is None:
            raise ValueError(
                f"The portfolio line ({pflineid}) does not exists for this portfolio ({pfid})."
            )
        elif tsname_tree != "notfound":
            return create_tstree(pfid, tsname_tree)

        # If not, use default.
        tsname_tree = self.pflines.get(pflineid, None)
        if tsname_tree is None:
            raise ValueError(
                f"The portfolio line ({pflineid}) does not exists for this portfolio ({pfid})."
            )
        return create_tstree(pfid, tsname_tree)

    def tstree_price(self, priceid: str) -> TsTree:
        """Timeseries that must be fetched to get the wanted price.

        Parameters
        ----------
        priceid : str
            Id of price.

        Returns
        -------
        TsTree
            Timeseries that must be fetched.
        """
        if priceid not in (avail := self.available_priceids()):
            raise ValueError(f"``priceid`` must be one of {', '.join(avail)}.")

        pfid = self.prices[priceid]["pfid"]
        tsname_tree = self.prices[priceid]["tsnames"]
        return create_tstree(pfid, tsname_tree)

    def available_pfids(self, original_only: bool = False) -> Iterable[str]:
        """All available portfolio ids.

        Parameters
        ----------
        original_only : bool, optional (default: False)
            If True, only return the ("original") portfolio ids that are present in belvis,
            and omit the ("synthetic") ones that are created by summing.

        Returns
        -------
        Iterable[str]
            List of portfolio ids that exist in this tenant, according to the configuration.
        """
        if original_only:
            return self.portfolios.original
        else:
            return [*self.portfolios.original, *self.portfolios.synthetic.keys()]

    def to_original_pfids(self, pfid: str) -> Iterable[str]:
        """The original pfids that need to be added to get values of wanted pfid.

        Parameters
        ----------
        pfid : str
            Id of portfolio. May be original or synthetic.

        Returns
        -------
        Iterable[str]
            List of original portfolio ids.
        """
        if pfid in self.portfolios.original:
            return [pfid]
        elif pfid in self.portfolios.synthetic:
            pfids = []
            for child_pfid in self.portfolios.synthetic[pfid]:
                for pfid in self.to_original_pfids(child_pfid):
                    pfids.append(pfid)
            return pfids
        raise ValueError(
            f"Could not find portfolio id {pfid} in configuration for this tenant; "
            f"expected one of {', '.join((*self.portfolios.original, *self.portfolios.synthetic))}."
        )

    def available_pflineids(self, pfid: str) -> Iterable[str]:
        """All available portfolio line ids for a given portfolio.

        Parameters
        ----------
        pfid : str
            Id of portfolio. May be original or synthetic.

        Returns
        -------
        Iterable[str]
            Set of portfolio line ids that exist in this tenant and portfolio, according
            to the configuration.
        """
        if pfid in self.portfolios.original:
            # Default.
            pflineids = set(self.pflines.keys())
            # Corrections.
            for pflineid, tsnames in self.corrections.get(pfid, {}).items():
                if tsnames is None:
                    pflineids.remove(pflineid)
                else:
                    pflineids.add(pflineid)
            # Return.
            return pflineids
        else:
            # Only keep those pflineids that are present in all summands.
            original_pfids = self.to_original_pfids(pfid)
            return list(
                set.intersection(
                    *[self.available_pflineids(pfid) for pfid in original_pfids]
                )
            )

    def available_priceids(self) -> Iterable[str]:
        """All available price ids for this tenant.

        Parameters
        ----------
        None

        Returns
        -------
        Iterable[str]
            List of price ids that exist in this tenant, according to the configuration.
        """
        return self.prices.keys()
