from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import Config


def create_engine_and_session(url: str):
    engine = create_async_engine(url, echo=False, pool_size=10, max_overflow=20)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, session_factory


_engine = None
_session_factory = None


async def init_db(config: Config):
    global _engine, _session_factory
    _engine, _session_factory = create_engine_and_session(config.DATABASE_URL)

    async with _engine.begin() as conn:
        from db.models import Base
        await conn.run_sync(Base.metadata.create_all)

    return _engine, _session_factory


async def close_db():
    global _engine
    if _engine:
        await _engine.dispose()


async def get_session() -> AsyncSession:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    async with _session_factory() as session:
        yield session
