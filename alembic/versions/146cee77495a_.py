"""empty message

Revision ID: 146cee77495a
Revises: 81d58ac4ba3c
Create Date: 2023-03-09 15:29:19.231010

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '146cee77495a'
down_revision = '81d58ac4ba3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product_schedule', sa.Column('name', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_schedule', 'name')
    # ### end Alembic commands ###
