import datetime as dt


def print_status(msg: str):
    """Print current timestamp and status message ``msg`` to terminal."""
    print(f"{dt.datetime.now().isoformat()} {msg}")
