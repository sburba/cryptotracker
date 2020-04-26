"""create currency pair volume table

Revision ID: c14a6cd36ba8
Revises: 
Create Date: 2020-04-25 17:31:31.730662

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c14a6cd36ba8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "currency_pair_volumes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fetch_time", sa.types.DateTime(timezone=True), nullable=False),
        sa.Column("volume", sa.Numeric, nullable=False),
        sa.Column("currency_pair", sa.String, nullable=False),
    )


def downgrade():
    op.drop_table("currency_pair_volumes")
