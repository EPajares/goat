from typing import Any, Dict, Generic, List, Tuple, Type, TypeVar, Union
from uuid import UUID

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import RelationshipProperty, selectinload
from sqlalchemy.sql import Select

from core.db.models import (
    Folder,
    Job,
    Layer,
    Project,
    Scenario,
    Status,
    SystemSetting,
    User,
)
from core.schemas import OrderEnum
from core.schemas.folder import FolderCreate, FolderUpdate
from core.schemas.scenario import IScenarioCreate, IScenarioUpdate
from core.schemas.system_setting import SystemSettingsCreate, SystemSettingsUpdate

ModelType = TypeVar(
    "ModelType",
    bound=Layer | Project | User | Folder | Job | Scenario | Status | SystemSetting,
)
CreateSchemaType = TypeVar(
    "CreateSchemaType", bound=FolderCreate | SystemSettingsCreate | IScenarioCreate
)
UpdateSchemaType = TypeVar(
    "UpdateSchemaType", bound=FolderUpdate | SystemSettingsUpdate | IScenarioUpdate
)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def extend_statement(
        self, statement: Select[Any], *, extra_fields: List[Any] = []
    ) -> Select[Any]:
        for field in extra_fields:
            if (
                hasattr(field, "property")
                and isinstance(field.property, RelationshipProperty)
                and hasattr(self.model, field.key)
            ):
                statement = statement.options(selectinload(field))
        return statement

    async def get(
        self, db: AsyncSession, id: Any, extra_fields: List[Any] = []
    ) -> ModelType | None:
        statement = select(self.model).where(self.model.id == id)
        statement = self.extend_statement(statement, extra_fields=extra_fields)
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, *, extra_fields: List[Any] = []
    ) -> List[ModelType]:
        statement = select(self.model)
        statement = self.extend_statement(statement, extra_fields=extra_fields)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_multi_keys(
        self, db: AsyncSession, *, keys: Dict[str, Any], extra_fields: List[Any] = []
    ) -> List[ModelType]:
        """
        Example of usage:
        get_by_multi_keys(db, keys={"name": "John", "age": 2})
        """

        statement = select(self.model)
        for key, value in keys.items():
            statement = statement.where(getattr(self.model, key) == value)
        statement = self.extend_statement(statement, extra_fields=extra_fields)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        query: Select[Any] | None = None,
        page_params: Params | None = None,
        order_by: str | None = None,
        order: OrderEnum | None = OrderEnum.ascendent,
        extra_fields: List[Any] = [],
        search_text: Dict[str, Any] | None = None,
    ) -> Page[ModelType] | List[Tuple[ModelType]]:
        if query is None:
            query = select(self.model)
        query = self.extend_statement(query, extra_fields=extra_fields)
        assert type(query) is Select

        # Search for text in specified column
        if search_text is not None:
            search_query = []
            for key, value in search_text.items():
                # Search for text in specified column make both input and column lowercase
                search_query.append(
                    func.lower(getattr(self.model, key)).contains(value.lower())
                )
            query = query.where(or_(*search_query))

        columns = self.model.__table__.columns
        if order_by and order_by in columns:
            if order == OrderEnum.ascendent:
                query = query.order_by(columns[order_by].asc())
            else:
                query = query.order_by(columns[order_by].desc())

        if page_params is None:
            result = await db.execute(query)
            items: List[Tuple[ModelType]] = []
            for row in result.all():
                items.append(tuple(row))
            return items
        else:
            result = await paginate(db, query, page_params)

            if not isinstance(result, Page):
                raise ValueError("Invalid paginated result.")

            return result

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model.model_validate(obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]] | None = None,
    ) -> ModelType:
        fields: List[str]
        if isinstance(obj_in, dict):
            update_data = obj_in
            fields = list(obj_in.keys())
        elif isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True)
            fields = list(type(obj_in).model_fields.keys())
        elif obj_in is None:
            update_data = {}
            fields = []
        else:
            raise ValueError(
                "Obj_in must be either a dict or a Pydantic model or None."
            )

        for field in fields:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Create a new object from the updated object to validate it in case the layer has validators.
        if (
            hasattr(self.model, "__pydantic_decorators__")
            and self.model.__pydantic_decorators__.validators
        ):
            try:
                validated_obj = self.model(**db_obj.model_dump())
                for field in self.model.model_fields.keys():
                    setattr(db_obj, field, getattr(validated_obj, field))
            except ValidationError as e:
                raise e
        return db_obj

    async def update_multi(
        self,
        db: AsyncSession,
        *,
        db_objs: ModelType,
        objs_in: List[Union[UpdateSchemaType, Dict[str, Any]]],
    ) -> List[ModelType]:
        """Update multiple objects at once by id."""
        ids = []
        # Loop through all db_objs and objs_in and update the db_obj with the obj_in.
        for db_obj, obj_in in zip(db_objs, objs_in, strict=True):
            if isinstance(obj_in, dict):
                update_data = obj_in
                fields = obj_in.keys()
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
                fields = type(obj_in).model_fields.keys()
            for field in fields:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            db.add(db_obj)
            ids.append(db_obj.id)
        await db.commit()

        # Get objects again to return them. Refresh cannot be used as it only returns one object.
        ids = [db_obj.id for db_obj in db_objs]
        statement = select(self.model).where(self.model.id.in_(ids))
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def remove(self, db: AsyncSession, *, id: int | UUID) -> ModelType:
        obj = await db.get(self.model, id)

        if not obj:
            raise ValueError(f"Object with id {id} not found.")

        await db.delete(obj)
        await db.commit()
        return obj

    async def delete(self, db: AsyncSession, *, id: int | UUID) -> ModelType:
        return await self.remove(db, id=id)

    async def count(self, db: AsyncSession) -> int:
        """
        Count the number of rows in the table.
        """
        statement = select(func.count(self.model.id))
        result = await db.execute(statement)
        return result.scalar_one()
