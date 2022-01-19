"""create invite table

Revision ID: fcb4ea0fce29
Revises: 90aa88820eab
Create Date: 2022-01-18 02:16:53.954662

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fcb4ea0fce29'
down_revision = '90aa88820eab'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('invite',
    sa.Column('client', sa.String(255), sa.ForeignKey("client.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    sa.Column('room', sa.String(255), nullable=False, primary_key=True),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('inviter', sa.String(255), nullable=False)
    )


def downgrade():
    op.drop_table('invite')
