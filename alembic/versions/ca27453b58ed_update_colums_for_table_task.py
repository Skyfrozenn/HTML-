"""update colums for table task

Revision ID: ca27453b58ed
Revises: 82b473cc8499
Create Date: 2025-07-12 18:34:47.776075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca27453b58ed'
down_revision: Union[str, Sequence[str], None] = '82b473cc8499'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Для SQLite используем batch_alter_table
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column('updated_at',
            existing_type=sa.DATETIME(),
            type_=sa.String(),
            nullable=True,
            postgresql_using='updated_at::text',
            server_default="Не изменялось")
        
        batch_op.alter_column('completed_at',
            existing_type=sa.DATETIME(),
            type_=sa.String(),
            nullable=True,
            postgresql_using='completed_at::text',
            server_default="Не выполнено")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column('completed_at',
            existing_type=sa.String(),
            type_=sa.DATETIME(),
            nullable=True,
            server_default=None)
            
        batch_op.alter_column('updated_at',
            existing_type=sa.String(),
            type_=sa.DATETIME(),
            nullable=True,
            server_default=None)