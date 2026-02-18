"""Enable ltree

Revision ID: d10db9094acf
Revises: 8f64d6110123
Create Date: 2026-02-16 11:44:05.267601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd10db9094acf'
down_revision: Union[str, Sequence[str], None] = '8f64d6110123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS ltree")
