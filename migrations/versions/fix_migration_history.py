"""fix migration history

Revision ID: fix_migration_001
Revises: f4881cfb8a19
Create Date: 2023-12-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_migration_001'
down_revision = 'f4881cfb8a19'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 这里不需要手动修改版本号，alembic会自动处理
    pass

def downgrade() -> None:
    # 这里不需要手动修改版本号，alembic会自动处理
    pass 