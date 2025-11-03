import os
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, List, Set

from psycopg2.errors import UndefinedFunction
from sqlalchemy import Connection, text


class FunctionManager:
    def __init__(
        self,
        engine: Connection,
        path: str,
        schema: str,
        schema_mapping: Dict[str, Any] | None = None,
    ) -> None:
        self.engine = engine
        self.path = path
        self.schema = schema
        if schema_mapping:
            self.schema_mapping = schema_mapping
        else:
            self.schema_mapping = {schema: schema}

    def find_unapplied_dependencies(
        self, function_content: str, function_list: List[Any]
    ) -> Set[str]:
        dependencies = set()
        for function in function_list:
            if "." + function.name in function_content:
                dependencies.add(function.name)
        return dependencies

    def get_name_from_path(self, path: Path) -> str:
        """
        to get name of function from path (file name)
        """
        basename = os.path.basename(path)
        return os.path.splitext(basename)[0]

    def get_function_list_from_files(self, path_list: List[Path]) -> List[Any]:
        function = namedtuple("function", ["path", "name", "dependencies"])
        function_list = []
        for path in path_list:
            function_name = self.get_name_from_path(path)
            function_list.append(function(path, function_name, set()))
        return function_list

    def sorted_path_by_dependency(self, path_list: List[Path]) -> List[Path]:
        """
        The first function is not depended to any others.
        But the last one maybe depended.
        """
        new_path_list = []
        function_list = self.get_function_list_from_files(path_list)
        while function_list:
            function = function_list.pop(0)
            function_content = Path(function.path).read_text()
            dependencies = self.find_unapplied_dependencies(
                function_content, function_list
            )
            if dependencies:
                # found dependencies, add to the end of functions again.
                # update dependencies
                function.dependencies.clear()
                function.dependencies.update(dependencies)
                function_list.append(function)
            else:
                new_path_list.append(Path(function.path))

        return new_path_list

    def sql_function_entities(self) -> List[str]:
        sql_function_entities = []
        # Find all with the exception the ones in legacy
        function_paths = Path(str(Path().resolve()) + self.path).rglob("*.sql")
        function_paths_list: List[Path] = [
            p for p in function_paths if "legacy" not in str(p)
        ]
        for p in self.sorted_path_by_dependency(function_paths_list):
            sql_text = p.read_text()
            # Ensure that the function does not start with a comment
            if sql_text.startswith("/*") or sql_text.startswith("--"):
                raise ValueError(
                    f"Function {self.get_name_from_path(p)} has a comment at the beginning. Please remove it."
                )

            # If schema mapping is provided, replace the schema in the function
            if self.schema_mapping:
                for key in self.schema_mapping.keys():
                    sql_text = sql_text.replace(
                        f"{key}.", f"{self.schema_mapping[key]}."
                    )

            sql_function_entities.append(sql_text)
        return sql_function_entities

    def drop_functions(self) -> None:
        # Drop all functions in the schema
        stmt_list_functions = text(
            f"SELECT proname FROM pg_proc WHERE pronamespace = '{self.schema_mapping[self.schema]}'::regnamespace"
        )
        functions = self.engine.execute(stmt_list_functions).fetchall()
        functions = [f[0] for f in functions]
        for function in functions:
            # Skip trigger functions as they should be dropped by drop_triggers()
            if "trigger" in function:
                continue
            print(f"Dropping {function}()")
            statement = f"DROP FUNCTION IF EXISTS {self.schema_mapping[self.schema]}.{function} CASCADE;"
            try:
                self.engine.execute(text(statement))
            except UndefinedFunction as e:
                print(e)
        print(f"{len(functions)} functions dropped!")

    def add_functions(self) -> None:
        sql_function_entities_ = self.sql_function_entities()
        for function in sql_function_entities_:
            self.engine.execute(text(function))
            print("Adding Function.")
        print(f"{len(sql_function_entities_)} functions added!")

    def update_functions(self) -> None:
        # It will drop all functions and add them again
        self.drop_functions()
        print("##################################################")
        self.add_functions()
