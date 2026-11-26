"""create devices

Revision ID: 2c997572e58f
Revises: f511a0394d3e
Create Date: 2026-11-25 18:50:54.807312

"""

import sqlalchemy as sa

from alembic import op

revision: str = "2c997572e58f"
down_revision: str = "f511a0394d3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "devices",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=False),
        sa.Column("brand", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.CheckConstraint(
            "device_type ~ '[^[:space:]]'", name="ck_devices_device_type_not_blank"
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_devices_customer_id"), "devices", ["customer_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_devices_customer_id"), table_name="devices")
    op.drop_table("devices")
