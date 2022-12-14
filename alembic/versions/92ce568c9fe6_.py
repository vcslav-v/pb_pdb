"""empty message

Revision ID: 92ce568c9fe6
Revises: fc10910deea9
Create Date: 2022-12-12 17:59:47.209119

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92ce568c9fe6'
down_revision = 'fc10910deea9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('trello_link', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'trello_link')
    # ### end Alembic commands ###
