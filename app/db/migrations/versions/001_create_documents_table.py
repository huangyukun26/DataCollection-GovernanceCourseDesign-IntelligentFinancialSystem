"""create documents table

Revision ID: 001
Revises: 
Create Date: 2024-03-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(20), nullable=True),
        sa.Column('doc_number', sa.String(50), nullable=True),
        sa.Column('file_path', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(
        'ix_documents_doc_type',
        'documents',
        ['doc_type']
    )
    op.create_index(
        'ix_documents_doc_number',
        'documents',
        ['doc_number']
    )

def downgrade():
    op.drop_index('ix_documents_doc_number')
    op.drop_index('ix_documents_doc_type')
    op.drop_table('documents') 