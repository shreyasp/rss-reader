# built-in imports
from collections.abc import AsyncGenerator

# external imports
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

async def get_db_session(pg_conn_str: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(pg_conn_str)
    factory = async_sessionmaker(engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except exc.SQLAlchemyError as error:
            await session.rollback()
            raise(error)