from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from step_database import DatabaseStep, DatabaseUnavailable


def test_unreachable_database_raises_unavailable() -> None:
    # Port 1'de dinleyen sunucu yok: bağlantı hemen OperationalError ile reddedilir.
    engine = create_engine(
        "postgresql+psycopg://u:p@127.0.0.1:1/db", connect_args={"connect_timeout": 2}
    )

    with pytest.raises(DatabaseUnavailable):
        DatabaseStep(engine).get_participant_by_key("ali")


def test_pool_timeout_raises_unavailable() -> None:
    engine = create_engine("postgresql+psycopg://u:p@127.0.0.1:1/db")
    with patch("step_database.Session", side_effect=PoolTimeoutError("havuz dolu")):
        with pytest.raises(DatabaseUnavailable):
            DatabaseStep(engine).get_participant_by_key("ali")
