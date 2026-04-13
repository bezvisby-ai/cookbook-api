import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionLocal, engine, get_db, init_db
from .models import Recipe
from .schemas import (
    RecipeCreate,
    RecipeDetail,
    RecipeListItem,
    RecipeResponse,
)

SEED_RECIPES = [
    {
        "name": "Борщ украинский",
        "description": "Классический борщ со свеклой и капустой",
        "ingredients": [
            "говядина 500г",
            "капуста 300г",
            "свёкла 200г",
            "морковь 100г",
            "картофель 300г",
        ],
        "cooking_time": 120,
        "views": 50,
    },
    {
        "name": "Салат Оливье",
        "description": "Традиционный новогодний салат",
        "ingredients": [
            "картофель 300г",
            "морковь 200г",
            "яйца 4 шт",
            "колбаса варёная 300г",
            "горошек 1 банка",
        ],
        "cooking_time": 30,
        "views": 100,
    },
    {
        "name": "Пельмени домашние",
        "description": "Сочные пельмени с мясом",
        "ingredients": [
            "мука 500г",
            "яйца 2 шт",
            "вода 150мл",
            "фарш 500г",
            "лук 1 шт",
        ],
        "cooking_time": 90,
        "views": 30,
    },
    {
        "name": "Шаурма",
        "description": "Домашняя шаурма с курицей",
        "ingredients": [
            "куриное филе 400г",
            "лаваш 2 шт",
            "огурец 1 шт",
            "помидор 1 шт",
            "капуста 200г",
        ],
        "cooking_time": 25,
        "views": 80,
    },
    {
        "name": "Плов",
        "description": "Рассыпчатый плов с бараниной",
        "ingredients": [
            "рис 400г",
            "баранина 500г",
            "лук 2 шт",
            "морковь 2 шт",
            "чеснок 1 головка",
        ],
        "cooking_time": 60,
        "views": 45,
    },
]


async def seed_data():
    """Заполнение БД начальными данными."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Recipe))
        if result.scalars().first() is None:
            for recipe_data in SEED_RECIPES:
                recipe = Recipe(
                    name=recipe_data["name"],
                    description=recipe_data["description"],
                    ingredients=json.dumps(
                        recipe_data["ingredients"], ensure_ascii=False
                    ),
                    cooking_time=recipe_data["cooking_time"],
                    views=recipe_data["views"],
                )
                session.add(recipe)
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения: инициализация и очистка."""
    await init_db()
    await seed_data()
    yield
    await engine.dispose()


app = FastAPI(
    title="🍳 Кулинарная книга",
    description="""
## API Кулинарной книги

REST API для управления рецептами.

### Основные эндпоинты:
- `GET /recipes` — список всех рецептов
- `GET /recipes/{id}` — детальная информация о рецепте
- `POST /recipes` — создание нового рецепта

### Сортировка:
Рецепты сортируются по количеству просмотров (DESC).
При равных просмотрах — по времени приготовления (ASC).
    """,
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/recipes",
    summary="Получить список всех рецептов",
    description="""
Возвращает список всех рецептов из базы данных.

### Сортировка:
- По умолчанию: по количеству просмотров (DESC), затем по времени приготовления (ASC)
- Популярные рецепты (с большим количеством просмотров) показываются первыми

### Экран 1 — Таблица:
Этот эндпоинт возвращает данные для таблицы на главном экране:
- Название блюда
- Количество просмотров
- Время приготовления (в минутах)

### Возвращает:
Список рецептов с полями: id, name, views, cooking_time
    """,
)
async def get_recipes(db: AsyncSession = Depends(get_db)):
    """
    Получение списка всех рецептов.

    Сортировка: по просмотрам (DESC), затем по времени (ASC)
    """
    query = select(Recipe).order_by(
        Recipe.views.desc(), Recipe.cooking_time.asc()
    )
    result = await db.execute(query)
    recipes = result.scalars().all()
    return [RecipeListItem.model_validate(r) for r in recipes]


@app.get(
    "/recipes/{recipe_id}",
    summary="Получить детальную информацию о рецепте",
    description="""
Возвращает полную информацию о рецепте по его ID.

### Экран 2 — Детальная информация:
Этот эндпоинт возвращает данные для страницы рецепта:
- Название блюда
- Время приготовления (в минутах)
- Список ингредиентов
- Текстовое описание рецепта
- Количество просмотров
- Дата создания

### Побочный эффект:
При каждом вызове счётчик просмотров увеличивается на 1.

### Ошибки:
- 404: Рецепт не найден
    """,
)
async def get_recipe_detail(recipe_id: int, db: AsyncSession = Depends(get_db)):
    """
    Получение детальной информации о рецепте.

    При каждом запросе увеличивает счётчик просмотров.

    Raises:
        HTTPException 404: если рецепт не найден
    """
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    await db.execute(
        update(Recipe)
        .where(Recipe.id == recipe_id)
        .values(views=Recipe.views + 1)
    )
    await db.commit()
    recipe.views += 1  # type: ignore[assignment]

    ingredients = None
    if recipe.ingredients:
        try:
            ingredients = json.loads(recipe.ingredients)  # type: ignore[arg-type]
        except json.JSONDecodeError:
            ingredients = [recipe.ingredients]  # type: ignore[list-item]

    return RecipeDetail(
        id=recipe.id,  # type: ignore[arg-type]
        name=recipe.name,  # type: ignore[arg-type]
        cooking_time=recipe.cooking_time,  # type: ignore[arg-type]
        ingredients=ingredients,  # type: ignore[arg-type]
        description=recipe.description,  # type: ignore[arg-type]
        views=recipe.views,  # type: ignore[arg-type]
        created_at=recipe.created_at,  # type: ignore[arg-type]
    )


@app.post(
    "/recipes",
    status_code=201,
    summary="Создать новый рецепт",
    description="""
Создаёт новый рецепт в базе данных.

### Обязательные поля:
- `name`: название блюда (строка, 1-255 символов)
- `cooking_time`: время приготовления в минутах (целое число >= 0)
- `description`: текстовое описание рецепта
- `ingredients`: список ингредиентов (массив строк)

### После создания:
- Рецепту присваивается уникальный ID
- Счётчик просмотров = 0
- Проставляется дата создания

### Возвращает:
ID созданного рецепта, название и сообщение об успехе.
    """,
)
async def create_recipe(
    recipe_data: RecipeCreate, db: AsyncSession = Depends(get_db)
):
    """
    Создание нового рецепта.

    Все поля обязательны: name, cooking_time, description, ingredients.
    """
    new_recipe = Recipe(
        name=recipe_data.name,
        description=recipe_data.description,
        ingredients=json.dumps(
            recipe_data.ingredients, ensure_ascii=False
        ),
        cooking_time=recipe_data.cooking_time,
        views=0,
    )

    db.add(new_recipe)
    await db.commit()
    await db.refresh(new_recipe)

    return RecipeResponse(
        id=new_recipe.id,  # type: ignore[arg-type]
        name=new_recipe.name,  # type: ignore[arg-type]
        message="Рецепт создан",
    )

