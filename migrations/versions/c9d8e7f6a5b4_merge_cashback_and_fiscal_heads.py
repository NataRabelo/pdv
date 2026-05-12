"""merge cashback and fiscal heads

Revision ID: c9d8e7f6a5b4
Revises: a4f1c8d2e7b9, b3c4d5e6f7a8
Create Date: 2026-04-20 14:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c9d8e7f6a5b4"
down_revision = ("a4f1c8d2e7b9", "b3c4d5e6f7a8")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
