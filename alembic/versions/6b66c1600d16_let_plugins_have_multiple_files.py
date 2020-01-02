"""Let plugins have multiple files

Revision ID: 6b66c1600d16
Revises: d295f8dcfa64
Create Date: 2020-01-02 01:30:51.622962

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6b66c1600d16"
down_revision = "d295f8dcfa64"
branch_labels = None
depends_on = None


def upgrade():
    plugin_file: sa.Table = op.create_table(
        "plugin_file",
        sa.Column("plugin_id", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(("plugin_id",), ["plugin.id"], onupdate="CASCADE",
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plugin_id", "file_name"))

    conn: sa.engine.Connection = op.get_bind()
    conn.execute(plugin_file.insert().values([{
        "plugin_id": plugin_id,
        "file_name": "config.yaml",
        "content": config
    } for plugin_id, config in conn.execute("SELECT id, config FROM plugin").fetchall()]))

    op.drop_column("plugin", "config")


def downgrade():
    op.add_column("plugin", sa.Column("config", sa.TEXT(), autoincrement=False, nullable=False))
    op.drop_table("plugin_file")
