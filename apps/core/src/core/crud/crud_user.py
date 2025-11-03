from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from core.core.config import settings
from core.db.models.user import User
from core.schemas.layer import NumberColumnsPerType, UserDataTable
from core.utils import table_exists

from .base import CRUDBase


class CRUDUser(CRUDBase[User, Any, Any]):
    async def create_user_data_tables(
        self, async_session: AsyncSession, user_id: UUID
    ) -> None:
        """Create the user data tables."""
        # Don't create the network table for all users yet
        for table_type in (
            UserDataTable.point,
            UserDataTable.line,
            UserDataTable.polygon,
            UserDataTable.no_geometry,
        ):
            table_name = f"{table_type.value}_{str(user_id).replace('-', '')}"

            # Check if table exists
            if not await table_exists(
                async_session, settings.USER_DATA_SCHEMA, table_name
            ):
                # Create table
                if table_type.value == UserDataTable.no_geometry.value:
                    geom_column = ""
                    additional_columns = ""
                else:
                    geom_column = "geom GEOMETRY,"

                    if table_type.value == UserDataTable.street_network_line.value:
                        additional_columns = """
                            ,source integer NOT NULL
                            ,target integer NOT NULL
                            ,h3_3 integer NULL
                            ,h3_6 integer NOT NULL
                        """
                    elif table_type.value == UserDataTable.street_network_point.value:
                        additional_columns = """
                            ,connector_id integer NOT NULL
                            ,h3_3 integer NULL
                            ,h3_6 integer NOT NULL
                        """
                    else:
                        additional_columns = """
                            ,cluster_keep boolean
                            ,h3_3 integer NULL
                            ,h3_group h3index NULL
                        """

                # SQL for
                sql_create_table = f"""
                CREATE TABLE {settings.USER_DATA_SCHEMA}."{table_name}" (
                    id UUID DEFAULT basic.uuid_generate_v7() NOT NULL,
                    layer_id UUID NOT NULL,
                    {geom_column}
                    {', '.join([f'integer_attr{i+1} INTEGER' for i in range(NumberColumnsPerType.integer.value)])},
                    {', '.join([f'bigint_attr{i+1} BIGINT' for i in range(NumberColumnsPerType.bigint.value)])},
                    {', '.join([f'float_attr{i+1} FLOAT' for i in range(NumberColumnsPerType.float.value)])},
                    {', '.join([f'text_attr{i+1} TEXT' for i in range(NumberColumnsPerType.text.value)])},
                    {', '.join([f'jsonb_attr{i+1} jsonb' for i in range(NumberColumnsPerType.jsonb.value)])},
                    {', '.join([f'arrint_attr{i+1} INTEGER[]' for i in range(NumberColumnsPerType.arrint.value)])},
                    {', '.join([f'arrfloat_attr{i+1} FLOAT[]' for i in range(NumberColumnsPerType.arrfloat.value)])},
                    {', '.join([f'arrtext_attr{i+1} TEXT[]' for i in range(NumberColumnsPerType.arrtext.value)])},
                    {', '.join([f'timestamp_attr{i+1} TIMESTAMP' for i in range(NumberColumnsPerType.timestamp.value)])},
                    {', '.join([f'boolean_attr{i+1} BOOLEAN' for i in range(NumberColumnsPerType.boolean.value)])},
                    updated_at timestamptz NOT NULL DEFAULT to_char((CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD"T"HH24:MI:SSOF'::text)::timestamp with time zone,
                    created_at timestamptz NOT NULL DEFAULT to_char((CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD"T"HH24:MI:SSOF'::text)::timestamp with time zone
                    {additional_columns}
                );
                """
                await async_session.execute(text(sql_create_table))

                # Apply indices for standard spatial tables
                if table_type in (
                    UserDataTable.point.value,
                    UserDataTable.line.value,
                    UserDataTable.polygon.value,
                ):
                    # Create Trigger
                    sql_create_trigger = f"""CREATE TRIGGER trigger_{settings.USER_DATA_SCHEMA}_{table_name}
                        BEFORE INSERT OR UPDATE ON {settings.USER_DATA_SCHEMA}."{table_name}"
                        FOR EACH ROW EXECUTE FUNCTION basic.set_user_data_h3();
                    """
                    await async_session.execute(text(sql_create_trigger))
                    # Create Geospatial Index
                    await async_session.execute(
                        text(
                            f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" USING GIST(layer_id, geom);"""
                        )
                    )
                    # Create index for clustering
                    await async_session.execute(
                        text(
                            f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (layer_id, h3_group);"""
                        )
                    )
                    await async_session.execute(
                        text(
                            f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (layer_id, cluster_keep);"""
                        )
                    )
                    # Create Primary Key on ID
                    await async_session.execute(
                        text(
                            f"""ALTER TABLE {settings.USER_DATA_SCHEMA}."{table_name}" ADD PRIMARY KEY(id);"""
                        )
                    )
                # Create Index for street_segment and street_connector
                elif table_type in [
                    UserDataTable.street_network_point.value,
                    UserDataTable.street_network_line.value,
                ]:
                    # Create Geospatial Index
                    await async_session.execute(
                        text(
                            f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" USING GIST(h3_3, layer_id, geom);"""
                        )
                    )
                    # Create index for source and target
                    if table_type == UserDataTable.street_network_line.value:
                        await async_session.execute(
                            text(
                                f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (h3_3, layer_id, source);"""
                            )
                        )
                        await async_session.execute(
                            text(
                                f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (h3_3, layer_id, target);"""
                            )
                        )
                    if table_type == UserDataTable.street_network_point.value:
                        await async_session.execute(
                            text(
                                f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (h3_3, layer_id, connector_id);"""
                            )
                        )
                    # Create Index on ID
                    await async_session.execute(
                        text(
                            f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (h3_3, id);"""
                        )
                    )
                    # Make table distributed in case of street_segment and street_connector
                    await async_session.execute(
                        text(
                            f"""SELECT create_distributed_table('{settings.USER_DATA_SCHEMA}.{table_name}', 'h3_3');"""
                        )
                    )
                elif table_type == UserDataTable.no_geometry.value:
                    # Create index on layer_id
                    await async_session.execute(
                        text(
                            f"""CREATE INDEX ON {settings.USER_DATA_SCHEMA}."{table_name}" (layer_id);"""
                        )
                    )
                    # Create Primary Key on ID
                    await async_session.execute(
                        text(
                            f"""ALTER TABLE {settings.USER_DATA_SCHEMA}."{table_name}" ADD PRIMARY KEY(id);"""
                        )
                    )
            else:
                print(f"Table '{table_name}' already exists.")

        # Commit changes
        await async_session.commit()

    async def delete_user_data_tables(
        self, async_session: AsyncSession, user_id: UUID
    ) -> None:
        """Delete the user data tables."""

        for table_type in UserDataTable:
            table_name = f"{table_type.value}_{str(user_id).replace('-', '')}"

            # Check if table exists
            if await table_exists(async_session, settings.USER_DATA_SCHEMA, table_name):
                sql_delete_table = f"""
                DROP TABLE IF EXISTS {settings.USER_DATA_SCHEMA}."{table_name}";
                """
                await async_session.execute(text(sql_delete_table))
            else:
                print(f"Table '{table_name}' does not exist.")
        await async_session.commit()


user = CRUDUser(User)
