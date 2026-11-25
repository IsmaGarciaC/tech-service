"""create customers

Revision ID: f511a0394d3e
Revises:
Create Date: 2026-11-25 18:27:38.488789

"""

import sqlalchemy as sa

from alembic import op

revision: str = "f511a0394d3e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.CheckConstraint("name ~ '[^[:space:]]'", name="ck_customers_name_not_blank"),
        sa.CheckConstraint(
            "phone ~ '[^[:space:]]'", name="ck_customers_phone_not_blank"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("customers")
