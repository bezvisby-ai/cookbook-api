from sqlalchemy.ext.asyncio 
import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm 
import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///cookbook.db"

engine = create_async_engine(DATABASE_URL, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
