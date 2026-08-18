from typing import Generator
from sqlalchemy import URL, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import settings

# ---------------------------------------------------------------------------
# Primary Application Database (ai_scientist)
# ---------------------------------------------------------------------------
database_url = URL.create(
    drivername="mysql+pymysql",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
    query={"charset": "utf8mb4"},
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 5,
        "read_timeout": 5,
        "write_timeout": 5,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# External Data Warehouse (DWH) Database on Server 112
# ---------------------------------------------------------------------------
dwh_database_url = URL.create(
    drivername="mysql+pymysql",
    username=settings.dwh_db_user,
    password=settings.dwh_db_password,
    host=settings.dwh_db_host,
    port=settings.dwh_db_port,
    database=settings.dwh_db_name,
    query={"charset": "utf8mb4"},
)

dwh_engine = create_engine(
    dwh_database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 5,
        "read_timeout": 30,
        "write_timeout": 30,
    },
)

DwhSessionLocal = sessionmaker(
    bind=dwh_engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_dwh_db() -> Generator[Session, None, None]:
    db = DwhSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# External Data Lake Database on Server 112
# ---------------------------------------------------------------------------
datalake_database_url = URL.create(
    drivername="mysql+pymysql",
    username=settings.datalake_db_user,
    password=settings.datalake_db_password,
    host=settings.datalake_db_host,
    port=settings.datalake_db_port,
    database=settings.datalake_db_name,
    query={"charset": "utf8mb4"},
)

datalake_engine = create_engine(
    datalake_database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 5,
        "read_timeout": 30,
        "write_timeout": 30,
    },
)

DataLakeSessionLocal = sessionmaker(
    bind=datalake_engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_datalake_db() -> Generator[Session, None, None]:
    db = DataLakeSessionLocal()
    try:
        yield db
    finally:
        db.close()
