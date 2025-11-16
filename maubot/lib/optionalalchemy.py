try:
    from sqlalchemy import MetaData, asc, create_engine, desc
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import IntegrityError, OperationalError
except ImportError:

    class FakeError(Exception):
        pass

    class FakeType:
        def __init__(self, *args, **kwargs):
            raise Exception("SQLAlchemy is not installed")

    def create_engine(*args, **kwargs):
        raise Exception("SQLAlchemy is not installed")

    MetaData = Engine = FakeType
    IntegrityError = OperationalError = FakeError
    asc = desc = lambda a: a
