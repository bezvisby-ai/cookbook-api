import pytest
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
    async with AsyncClient(app=app, base_url="http://test") as ac:


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


class TestGetRecipes:
    @pytest.mark.asyncio
    async def test_get_empty_list(self, client):
        response = await client.get("/recipes")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_recipes(self, client, sample_recipe):
        response = await client.get("/recipes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Тестовый борщ"

    @pytest.mark.asyncio
    async def test_sorted_by_views(self, client, setup_database):
        async with TestAsyncSessionLocal() as session:
            session.add(Recipe(name="Мало", views=5, cooking_time=30))
            session.add(Recipe(name="Много", views=100, cooking_time=60))
            await session.commit()

        response = await client.get("/recipes")
        data = response.json()
        assert data[0]["name"] == "Много"
        assert data[1]["name"] == "Мало"


class TestGetRecipeDetail:
    @pytest.mark.asyncio
    async def test_get_detail(self, client, sample_recipe):
        response = await client.get(f"/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Тестовый борщ"
        assert data["ingredients"] == ["говядина", "капуста"]

    @pytest.mark.asyncio
    async def test_not_found(self, client):
        response = await client.get("/recipes/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_view_count(self, client, setup_database):
        async with TestAsyncSessionLocal() as session:
            recipe = Recipe(
                name="Тест",
                cooking_time=10,
                views=5,
                description="Описание тестового рецепта",
                ingredients='["ингредиент1", "ингредиент2"]',
            )
            session.add(recipe)
            await session.commit()
            await session.refresh(recipe)
            recipe_id = recipe.id

        r1 = await client.get(f"/recipes/{recipe_id}")
        r2 = await client.get(f"/recipes/{recipe_id}")
        assert r2.json()["views"] == r1.json()["views"] + 1


class TestCreateRecipe:
    @pytest.mark.asyncio
    async def test_create_full(self, client):
        response = await client.post(
            "/recipes",
            json={
                "name": "Новый салат",
                "description": "Простой салат",
                "ingredients": ["огурец", "помидор"],
                "cooking_time": 15,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новый салат"
        assert "создан" in data["message"]

    @pytest.mark.asyncio
    async def test_create_minimal(self, client):
        response = await client.post(
            "/recipes",
            json={
                "name": "Минимальный",
                "cooking_time": 5,
                "description": "Простой рецепт",
                "ingredients": [],
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_validation_error(self, client):
        response = await client.post(
            "/recipes", json={"name": "", "cooking_time": 10}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
