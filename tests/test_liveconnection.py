"""Tests for which a live connection is needed."""

import datetime as dt
import os
from typing import Iterable

import pytest

import belvys


def gettenants() -> Iterable[belvys.Tenant]:
    """Create tenants from data in environment variables."""

    def get_environ(key):
        value = os.environ.get(key)
        if value is None:
            raise ValueError(f"Key '{key}' not found in environment variables'")
        return value

    try:
        usr, pwd, server = (
            get_environ(key) for key in ("BELVIS_USR", "BELVIS_PWD", "BELVIS_SERVER_1")
        )
    except ValueError:
        return []

    tenants = []
    tenant_info = {
        "pwr": ("BELVIS_TENANT_1A", "BELVIS_STRUCT_1A"),
        "gas": ("BELVIS_TENANT_1B", "BELVIS_STRUCT_1B"),
    }
    for key, (tenant, filepath) in tenant_info.items():
        try:
            tenant, filepath = get_environ(tenant), get_environ(filepath)
        except ValueError:
            continue
        a = belvys.Api(server, tenant)
        a.access_from_usr_pwd(usr, pwd)
        s = belvys.Structure.from_file(filepath)
        tenant = belvys.Tenant(s, a)
        if key == "gas":

            def gas_aftercare(s, tsid, *args):
                if tsid == 23346575:
                    return s.tz_convert("+01:00").tz_localize(None)
                else:
                    return s

            tenant.prepend_aftercare(gas_aftercare)
        tenants.append(tenant)
    return tenants


@pytest.mark.parametrize("tenant", gettenants())
def test_all_pflines(tenant: belvys.Tenant):
    ts_left = dt.date.today() - dt.timedelta(days=30)
    ts_right = dt.date.today() + dt.timedelta(days=30)
    # Pflines
    for pfid in tenant.structure.available_pfids():
        for pflineid in tenant.structure.available_pflineids(pfid):
            print(pfid, pflineid)
            _ = tenant.portfolio_pfl(pfid, pflineid, ts_left, ts_right, True)
    # Prices
    for priceid in tenant.structure.available_priceids():
        print(priceid)
        _ = tenant.price_pfl(priceid, ts_left, ts_right)
