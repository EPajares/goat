"""Converted feature id to UUID

Revision ID: 2e3886888851
Revises: d376083e8c61
Create Date: 2024-07-21 17:01:47.058078

"""

from alembic import op
import sqlalchemy as sa
import geoalchemy2
import sqlmodel

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2e3886888851"
down_revision = "d376083e8c61"
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing 'feature_id' column
    op.drop_column("scenario_feature", "feature_id", schema="customer")

    # Add a new 'feature_id' column with UUID type
    op.add_column(
        "scenario_feature",
        sa.Column("feature_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="customer",
    )


def downgrade():
    # Drop the newly added 'feature_id' column with UUID type
    op.drop_column("scenario_feature", "feature_id", schema="customer")

    # Re-add the original 'feature_id' column with BIGINT type
    op.add_column(
        "scenario_feature",
        sa.Column("feature_id", sa.BIGINT(), nullable=True),
        schema="customer",
    )
