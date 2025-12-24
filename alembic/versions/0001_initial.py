"""Initial schema with date/time columns and indexes."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "seeds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("packets_made", sa.Integer(), nullable=True, default=0),
        sa.Column("seed_source", sa.String(), nullable=True),
        sa.Column("date_ordered", sa.Date(), nullable=True),
        sa.Column("date_finished", sa.Date(), nullable=True),
        sa.Column("date_cataloged", sa.Date(), nullable=True),
        sa.Column("date_ran_out", sa.Date(), nullable=True),
        sa.Column("amount_text", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seeds_type", "seeds", ["type"], unique=False)

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("seed_id", sa.Integer(), nullable=False),
        sa.Column("current_amount", sa.String(), nullable=True),
        sa.Column("buy_more", sa.Boolean(), nullable=True, default=False),
        sa.Column("extra", sa.Boolean(), nullable=True, default=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["seed_id"], ["seeds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("seed_id"),
    )
    op.create_index("ix_inventory_seed_id", "inventory", ["seed_id"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("seed_id", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False, server_default="Medium"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["seed_id"], ["seeds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_unique_constraint("uq_seed_task_type", "tasks", ["seed_id", "task_type"])
    op.create_index("ix_tasks_seed_id", "tasks", ["seed_id"], unique=False)
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"], unique=False)

    op.create_table(
        "inventory_adjustments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("seed_id", sa.Integer(), nullable=False),
        sa.Column("adjustment_type", sa.String(), nullable=False),
        sa.Column("amount_change", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("adjusted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["seed_id"], ["seeds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_adjustments_seed_id", "inventory_adjustments", ["seed_id"], unique=False)


def downgrade():
    op.drop_index("ix_inventory_adjustments_seed_id", table_name="inventory_adjustments")
    op.drop_table("inventory_adjustments")
    op.drop_index("ix_tasks_due_date", table_name="tasks")
    op.drop_index("ix_tasks_seed_id", table_name="tasks")
    op.drop_constraint("uq_seed_task_type", "tasks", type_="unique")
    op.drop_table("tasks")
    op.drop_index("ix_inventory_seed_id", table_name="inventory")
    op.drop_table("inventory")
    op.drop_index("ix_seeds_type", table_name="seeds")
    op.drop_table("seeds")
