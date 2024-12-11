"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2024-03-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 创建documents表
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(20)),
        sa.Column('doc_number', sa.String(50)),
        sa.Column('file_path', sa.String(255)),
        sa.Column('status', sa.String(20)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建invoices表
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(50), unique=True, index=True),
        sa.Column('invoice_code', sa.String(50)),
        sa.Column('seller', sa.String(100)),
        sa.Column('buyer', sa.String(100)),
        sa.Column('amount', sa.Numeric(15, 2)),
        sa.Column('tax_amount', sa.Numeric(15, 2)),
        sa.Column('total_amount', sa.Numeric(15, 2)),
        sa.Column('invoice_date', sa.Date()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('invoices')
    op.drop_table('documents') 