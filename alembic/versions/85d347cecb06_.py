"""empty message

Revision ID: 85d347cecb06
Revises: 
Create Date: 2022-09-16 19:15:36.790441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85d347cecb06'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('prefix', sa.Text(), nullable=True),
    sa.Column('number_products_created', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('prefix')
    )
    op.create_table('employees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trello_id', sa.Text(), nullable=True),
    sa.Column('full_name', sa.Text(), nullable=True),
    sa.Column('user_pick', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('trello_id')
    )
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trello_card_id', sa.Text(), nullable=True),
    sa.Column('readable_uid', sa.Text(), nullable=True),
    sa.Column('work_title', sa.Text(), nullable=True),
    sa.Column('cover', sa.LargeBinary(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('work_directory', sa.Text(), nullable=True),
    sa.Column('done', sa.Boolean(), nullable=True),
    sa.Column('designer_id', sa.Integer(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.ForeignKeyConstraint(['designer_id'], ['employees.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('readable_uid'),
    sa.UniqueConstraint('trello_card_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('products')
    op.drop_table('employees')
    op.drop_table('categories')
    # ### end Alembic commands ###
