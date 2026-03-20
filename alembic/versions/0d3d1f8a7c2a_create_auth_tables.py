"""create_auth_tables

Revision ID: 0d3d1f8a7c2a
Revises: 63aa39e6bb9c
Create Date: 2026-03-20 00:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0d3d1f8a7c2a"
down_revision: Union[str, Sequence[str], None] = "63aa39e6bb9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column("access_token_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("refresh_token_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "unverified_users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("last_activation_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activation_token_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_unverified_users_email", "unverified_users", ["email"], unique=True)

    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("access_token", sa.String(length=512), nullable=False),
        sa.Column("refresh_token", sa.String(length=512), nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "scopes",
            sa.dialects.postgresql.ARRAY(sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="unique_user_provider"),
    )


def downgrade() -> None:
    op.drop_table("oauth_tokens")
    op.drop_index("ix_unverified_users_email", table_name="unverified_users")
    op.drop_table("unverified_users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

