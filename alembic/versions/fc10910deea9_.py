"""empty message

Revision ID: fc10910deea9
Revises: b30561c9a624
Create Date: 2022-10-17 12:47:27.398156

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc10910deea9'
down_revision = 'b30561c9a624'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('market_place_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pixelbuddha', sa.Text(), nullable=True),
    sa.Column('creative_market', sa.Text(), nullable=True),
    sa.Column('you_work_for_them', sa.Text(), nullable=True),
    sa.Column('yellow_images', sa.Text(), nullable=True),
    sa.Column('designcuts', sa.Text(), nullable=True),
    sa.Column('elements', sa.Text(), nullable=True),
    sa.Column('art_station', sa.Text(), nullable=True),
    sa.Column('freepick', sa.Text(), nullable=True),
    sa.Column('adobe_stock', sa.Text(), nullable=True),
    sa.Column('graphicriver', sa.Text(), nullable=True),
    sa.Column('etsy', sa.Text(), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('market_place_links')
    # ### end Alembic commands ###
