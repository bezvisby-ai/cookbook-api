
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app
from app.models import Recipe

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestAsyncSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(setup_database):
   async with AsyncClient(app=app, base_url="http://test") as ac


@pytest_asyncio.fixture
async def sample_recipe(setup_database):
    async with TestAsyncSessionLocal() as session:
        recipe = Recipe(
            name="Тестовый борщ",
            description="Вкусный борщ",
            ingredients='["говядина", "капуста"]',
            cooking_time=120,
            views=10,
        )
        session.add(recipe)
        await session.commit()
        await session.refresh(recipe)
        return recipe
