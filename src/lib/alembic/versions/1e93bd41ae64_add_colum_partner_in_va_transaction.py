"""add colum partner in va_transaction

Revision ID: 1e93bd41ae64
Revises: 4c615e8d38ee
Create Date: 2023-10-18 16:42:35.893587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e93bd41ae64'
down_revision: Union[str, None] = '4c615e8d38ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('atom_va_transaction', sa.Column('partner', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('atom_va_transaction', 'partner')
    # ### end Alembic commands ###
