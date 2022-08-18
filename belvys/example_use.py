import belvys
import datetime as dt

# Define the structure of the belvis tenant and the timeseries we're interested in.
structure = belvys.Structure(
    freq="D",
    tz="Europe/Berlin",
    pflines={
        "current_offtake": "Offtake volume in MW",
        "expected_offtake": ["Offtake volume in MW", "Expected churn in MW"],
        "forward_sourced": [
            "Procurement forward volume in MW",
            "Procurement forward cost in EUR",
        ],
    },
    portfolios={
        "original": ["B2C_household", "B2C_Spot", "B2B_backtoback", "B2B_Spot"]
    },
    prices={
        "fwc_monthly_DE": {"pfid": "Germany", "tsnames": "MPFC (THE)"},
        "fwc_daily_DE": {"pfid": "Germany", "tsnames": ["MPFC (THE)", "M2D profile"]},
    },
)

# Define where and how to access the rest api.
api = belvys.Api("belvisserver01:8080", "gas")
api.access_from_usr_pwd("First.Lastname", "my_5tr0ngp@ssw0rd")

# Create Tenant instance to query the data.
tenant = belvys.Tenant(structure, api)

ts_left = dt.date.today() - dt.timedelta(days=10)
ts_right = dt.date.today() + dt.timedelta(days=10)
offtake = tenant.portfolio_pfl("B2C_household", "current_offtake", ts_left, ts_right)
prices = tenant.price_pfl("fwc_monthly_DE", ts_left, ts_right)
