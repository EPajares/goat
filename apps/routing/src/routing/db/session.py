from routing.core.config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

async_engine = create_async_engine(
    str(settings.ASYNC_SQLALCHEMY_DATABASE_URI), pool_pre_ping=True
)

async_session = async_sessionmaker(
    bind=async_engine, expire_on_commit=False, autoflush=False, autocommit=False
)
