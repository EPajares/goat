"""adjusted layerprojectlink

Revision ID: ea5778b147c4
Revises: d260d4b2c436
Create Date: 2023-09-04 06:04:42.699201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea5778b147c4'
down_revision = 'd260d4b2c436'
branch_labels = None
depends_on = None


def upgrade():
    # Add new column
    op.add_column('layer_project', sa.Column('name', sa.Text(), nullable=False), schema='customer')

    # Cast existing column data
    op.execute('ALTER TABLE customer.layer_project ALTER COLUMN query TYPE JSONB USING query::jsonb')

    # Drop column
    op.drop_column('layer_project', 'active', schema='customer')



def downgrade():
    # Add the 'active' column back
    op.add_column('layer_project', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=False), schema='customer')

    # Revert the column data type
    op.execute('ALTER TABLE customer.layer_project ALTER COLUMN query TYPE TEXT')  # Assuming you don't need a USING clause here

    # Drop the 'name' column
    op.drop_column('layer_project', 'name', schema='customer')

