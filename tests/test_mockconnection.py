"""Test using a mock server."""
import portfolyo as pf
import responses

import belvys


class MockAccess(belvys.Access):
    """Class to mock connection to Belvis server."""

    kinds = {
        34566: pf.Kind.VOLUME,
    }

    def request(url) -> responses.Response:
        pass


# TODO: finish!
