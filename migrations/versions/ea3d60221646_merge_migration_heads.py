"""merge migration heads

Revision ID: ea3d60221646
Revises: 0f6a8c2d4e9b, f9d0e1a2b3c4
Create Date: 2026-07-08 03:48:09.748855

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea3d60221646'
down_revision = ('0f6a8c2d4e9b', 'f9d0e1a2b3c4')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
