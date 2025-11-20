import os
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, List, Set

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AsyncFunctionManager:
    def __init__(
        self,
        session: AsyncSession,
        path: str,
        schema: str,
        schema_mapping: Dict[str, Any] | None = None,
    ) -> None:
        self.session = session
        self.path = path
        self.schema = schema
        self.schema_mapping = schema_mapping or {schema: schema}

    # ----------------------------------------------------------
    # Dependency resolution utilities
    # ----------------------------------------------------------
    def find_unapplied_dependencies(
        self, function_content: str, function_list: List[Any]
    ) -> Set[str]:
        return {
            function.name
            for function in function_list
            if f".{function.name}" in function_content
        }

    def get_name_from_path(self, path: Path) -> str:
        return os.path.splitext(os.path.basename(path))[0]

    def get_function_list_from_files(self, paths: List[Path]) -> List[Any]:
        fn = namedtuple("fn", ["path", "name", "dependencies"])
        return [fn(path, self.get_name_from_path(path), set()) for path in paths]

    def sorted_path_by_dependency(self, path_list: List[Path]) -> List[Path]:
        ordered: List[Path] = []
        function_list = self.get_function_list_from_files(path_list)

        while function_list:
            function = function_list.pop(0)
            content = Path(function.path).read_text()
            deps = self.find_unapplied_dependencies(content, function_list)

            if deps:
                function.dependencies.clear()
                function.dependencies.update(deps)
                function_list.append(function)
            else:
                ordered.append(Path(function.path))

        return ordered

    # ----------------------------------------------------------
    # Load SQL functions from files
    # ----------------------------------------------------------
    def sql_function_entities(self) -> List[str]:
        sql_entities = []

        root = Path(__file__).resolve().parent / self.path
        paths = [p for p in root.rglob("*.sql") if "legacy" not in str(p)]

        for p in self.sorted_path_by_dependency(paths):
            sql_text = p.read_text()

            if sql_text.startswith("/*") or sql_text.startswith("--"):
                raise ValueError(
                    f"Function {self.get_name_from_path(p)} may not begin with a comment."
                )

            for key, val in self.schema_mapping.items():
                sql_text = sql_text.replace(f"{key}.", f"{val}.")

            sql_entities.append(sql_text)

        return sql_entities

    # ----------------------------------------------------------
    # Async DROP / ADD
    # ----------------------------------------------------------
    async def drop_functions(self) -> None:
        stmt = text(
            f"SELECT proname FROM pg_proc "
            f"WHERE pronamespace = '{self.schema_mapping[self.schema]}'::regnamespace"
        )

        result = await self.session.execute(stmt)
        functions = [row[0] for row in result.fetchall()]

        for fn in functions:
            if "trigger" in fn:
                continue  # Skip trigger functions

            drop_stmt = text(
                f"DROP FUNCTION IF EXISTS {self.schema_mapping[self.schema]}.{fn} CASCADE;"
            )

            try:
                await self.session.execute(drop_stmt)
            except Exception as e:
                print(f"Error dropping {fn}: {e}")

        print(f"{len(functions)} functions dropped!")

    async def add_functions(self) -> None:
        sql_functions = self.sql_function_entities()

        for function_sql in sql_functions:
            try:
                await self.session.execute(text(function_sql))
                print("Adding function...")
            except Exception as e:
                print(f"Error adding function: {e}")

        print(f"{len(sql_functions)} functions added!")

    async def update_functions(self) -> None:
        await self.drop_functions()
        print("##################################################")
        await self.add_functions()
