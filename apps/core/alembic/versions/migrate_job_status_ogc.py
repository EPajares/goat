"""migrate job status to ogc compliant values

Revision ID: migrate_job_status_ogc
Revises: 44c27ff7ceb6
Create Date: 2024-12-30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "migrate_job_status_ogc"
down_revision: Union[str, None] = "44c27ff7ceb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate job table to OGC-compliant schema.

    1. Update status_simple values to OGC-compliant values
    2. Drop old columns (status JSONB, msg_simple, read, project_id)
    3. Rename status_simple to status
    """
    # Step 1: Update status_simple values to OGC-compliant values
    # pending -> accepted
    # finished -> successful
    # killed -> dismissed
    # timeout -> failed (timeout is a type of failure)
    op.execute("""
        UPDATE customer.job
        SET status_simple = CASE status_simple
            WHEN 'pending' THEN 'accepted'
            WHEN 'finished' THEN 'successful'
            WHEN 'killed' THEN 'dismissed'
            WHEN 'timeout' THEN 'failed'
            ELSE status_simple
        END
        WHERE status_simple IN ('pending', 'finished', 'killed', 'timeout')
    """)

    # Step 2: Drop old columns that are no longer in the model
    op.drop_column("job", "status", schema="customer")
    op.drop_column("job", "msg_simple", schema="customer")
    op.drop_column("job", "read", schema="customer")
    op.drop_column("job", "project_id", schema="customer")

    # Step 3: Rename status_simple to status
    op.alter_column("job", "status_simple", new_column_name="status", schema="customer")


def downgrade() -> None:
    """Revert OGC-compliant schema back to legacy schema."""
    # Step 1: Rename status back to status_simple
    op.alter_column("job", "status", new_column_name="status_simple", schema="customer")

    # Step 2: Re-add dropped columns
    op.add_column(
        "job",
        sa.Column("status", postgresql.JSONB(), nullable=True),
        schema="customer",
    )
    op.add_column(
        "job",
        sa.Column("msg_simple", sa.Text(), nullable=True),
        schema="customer",
    )
    op.add_column(
        "job",
        sa.Column("read", sa.Boolean(), nullable=True, server_default="false"),
        schema="customer",
    )
    op.add_column(
        "job",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="customer",
    )

    # Step 3: Revert OGC-compliant values back to legacy values
    op.execute("""
        UPDATE customer.job
        SET status_simple = CASE status_simple
            WHEN 'accepted' THEN 'pending'
            WHEN 'successful' THEN 'finished'
            WHEN 'dismissed' THEN 'killed'
            ELSE status_simple
        END
        WHERE status_simple IN ('accepted', 'successful', 'dismissed')
    """)
