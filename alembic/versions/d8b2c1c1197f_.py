"""empty message

Revision ID: d8b2c1c1197f
Revises: 1328bfc38deb
Create Date: 2025-01-29 14:09:34.102858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8b2c1c1197f'
down_revision = '1328bfc38deb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('is_extra', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'is_extra')
    # ### end Alembic commands ###
