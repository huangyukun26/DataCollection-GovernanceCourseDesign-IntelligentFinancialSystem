"""initial_migration

Revision ID: 6c2fb2974b04
Revises: 
Create Date: 2024-12-17 21:47:35.222011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c2fb2974b04'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('invoice_code', sa.String(length=50), nullable=True),
    sa.Column('invoice_number', sa.String(length=50), nullable=True),
    sa.Column('invoice_date', sa.String(length=20), nullable=True),
    sa.Column('total_amount', sa.String(length=20), nullable=True),
    sa.Column('tax_amount', sa.String(length=20), nullable=True),
    sa.Column('seller', sa.String(length=200), nullable=True),
    sa.Column('buyer', sa.String(length=200), nullable=True),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoices'))
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_code'), 'invoices', ['invoice_code'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_invoices_invoice_number'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_invoice_code'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_id'), table_name='invoices')
    op.drop_table('invoices')
    # ### end Alembic commands ###
