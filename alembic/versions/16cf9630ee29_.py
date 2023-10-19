"""empty message

Revision ID: 16cf9630ee29
Revises: 3996edc31fc9
Create Date: 2023-10-19 09:06:35.412439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16cf9630ee29'
down_revision = '3996edc31fc9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('adobe_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'adobe_count')
    # ### end Alembic commands ###