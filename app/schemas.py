from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class RecipeCreate(BaseModel):
    """
    Схема для создания нового рецепта.

    Все поля обязательны:
    - name: название блюда (строка, 1-255 символов)
    - cooking_time: время приготовления в минутах
    - description: текстовое описание рецепта
    - ingredients: список ингредиентов
    """

    name: str = Field(min_length=1, max_length=255, description="Название блюда")
    description: str = Field(
        description="Текстовое описание рецепта (пошаговое приготовление)"
    )
    ingredients: List[str] = Field(description="Список ингредиентов блюда")
    cooking_time: int = Field(ge=0, description="Время приготовления в минутах")


class RecipeListItem(BaseModel):
    """
    Схема элемента списка рецептов (таблица на главном экране).

    Содержит:
    - id: идентификатор рецепта
    - name: название блюда
    - views: количество просмотров
    - cooking_time: время приготовления
    """

    model_config = {"from_attributes": True}

    id: int = Field(description="Уникальный идентификатор рецепта")
    name: str = Field(description="Название блюда")
    views: int = Field(ge=0, description="Количество просмотров рецепта")
    cooking_time: int = Field(ge=0, description="Время приготовления в минутах")


class RecipeDetail(BaseModel):
    """
    Схема детальной информации о рецепте (второй экран).

    Содержит все поля рецепта:
    - основная информация (id, name, cooking_time)
    - список ингредиентов
    - текстовое описание
    - статистика (views, created_at)
    """

    model_config = {"from_attributes": True}

    id: int = Field(description="Уникальный идентификатор рецепта")
    name: str = Field(description="Название блюда")
    cooking_time: int = Field(ge=0, description="Время приготовления в минутах")
    ingredients: List[str] = Field(description="Список ингредиентов блюда")
    description: str = Field(description="Текстовое описание рецепта")
    views: int = Field(ge=0, description="Количество просмотров рецепта")
    created_at: datetime = Field(description="Дата и время создания рецепта")


class RecipeResponse(BaseModel):
    """
    Ответ API после успешного создания рецепта.
    """

    id: int = Field(description="ID созданного рецепта")
    name: str = Field(description="Название созданного рецепта")
    message: str = Field(description="Сообщение об успешной операции")
