"""Add ocr_index column, remove unique constraint on crop_id

Fixes BUG-14: OCR duplicate results issue where only 1 of 5 entries
per crop was being stored due to UNIQUE constraint on crop_id.

- Adds ocr_index column (0-4 for 5 signatures per crop)
- Removes UNIQUE constraint from crop_id
- Sets default ocr_index=0 for backward compatibility

Corrective edit (pre-release): this revision never applied on any
alembic-tracked database — fresh PostgreSQL and SQLite chains both aborted
here (the constraint dropped below was auto-named by PostgreSQL and cannot
be ALTER-dropped on SQLite), and runtime provisioning used create_all,
which does not track alembic_version.

Revision ID: 20260317140000
Revises: 20260312210000
Create Date: 2026-03-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260317140000"
down_revision: str | Sequence[str] | None = "20260312210000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Batch mode needs names for unnamed reflected constraints; SQLite leaves
# inline UNIQUE and FK constraints unnamed, so name them on re-render.
_BATCH_NAMING_CONVENTION = {
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def _find_pg_unique_on_crop_id(connection: sa.Connection) -> list[tuple[str, str]]:
    """Return (name, kind) for unique constraints and standalone unique
    indexes on ocr_results whose key columns are exactly {crop_id}, found
    structurally (catalog joins, not name or definition matching).

    Index classification uses indnkeyatts and indexprs so INCLUDE columns
    and expression indexes are handled correctly: a matching index has
    exactly one key attribute (INCLUDE columns are non-key), that attribute
    is crop_id, and no expressions. Indexes backing a unique constraint are
    excluded — they disappear with the constraint itself.
    """
    constraints = connection.execute(
        sa.text(
            "SELECT conname FROM pg_constraint con "
            "JOIN pg_attribute att ON att.attrelid = con.conrelid "
            " AND att.attnum = ANY(con.conkey) "
            "WHERE con.conrelid = 'ocr_results'::regclass "
            "AND con.contype = 'u' "
            "GROUP BY con.oid, con.conname "
            "HAVING count(*) = 1 AND max(att.attname) = 'crop_id'"
        )
    ).scalars()
    indexes = connection.execute(
        sa.text(
            "SELECT idx.relname FROM pg_index ix "
            "JOIN pg_class idx ON idx.oid = ix.indexrelid "
            "WHERE ix.indrelid = 'ocr_results'::regclass "
            "AND ix.indisunique AND NOT ix.indisprimary "
            "AND NOT EXISTS (SELECT 1 FROM pg_constraint con "
            " WHERE con.conindid = ix.indexrelid) "
            "AND ix.indnkeyatts = 1 "
            "AND ix.indexprs IS NULL "
            "AND (SELECT att.attname FROM pg_attribute att "
            " WHERE att.attrelid = ix.indrelid "
            " AND att.attnum = ix.indkey[0]) = 'crop_id'"
        )
    ).scalars()
    return [
        *[(name, "constraint") for name in constraints.all()],
        *[(name, "index") for name in indexes.all()],
    ]


def _find_crop_id_unique_constraint(connection: sa.Connection) -> str | None:
    """Return the name of the unique constraint on ocr_results.crop_id, if any.

    The base migration created the constraint unnamed: PostgreSQL auto-named
    it, so look up the actual name in the catalog. SQLite reflects it with a
    null name, so return the name batch mode assigns via the naming
    convention instead.
    """
    if connection.dialect.name == "postgresql":
        targets = _find_pg_unique_on_crop_id(connection)
        return targets[0][0] if targets else None
    inspector = sa.inspect(connection)
    for constraint in inspector.get_unique_constraints("ocr_results"):
        if constraint.get("column_names") == ["crop_id"]:
            return constraint.get("name") or "uq_ocr_results_crop_id"
    return None


def _assert_crop_id_not_unique(connection: sa.Connection) -> None:
    """Unconditional postcondition: after upgrade there must be no unique
    constraint and no single-column unique index on ocr_results.crop_id, so
    a silent BUG-14 regression cannot drop OCR rows unnoticed.
    """
    inspector = sa.inspect(connection)
    for constraint in inspector.get_unique_constraints("ocr_results"):
        if constraint.get("column_names") == ["crop_id"]:
            raise RuntimeError(
                "Unique constraint on ocr_results.crop_id still present "
                f"after removal attempt: {constraint.get('name')!r}"
            )
    for index in inspector.get_indexes("ocr_results"):
        if index.get("unique") and index.get("column_names") == ["crop_id"]:
            raise RuntimeError(
                "Unique index on ocr_results.crop_id still present "
                f"after removal attempt: {index.get('name')!r}"
            )


def _drop_unique_on_crop_id(connection: sa.Connection) -> None:
    """Drop every unique constraint and standalone unique index on
    ocr_results.crop_id (PG), or the reflected constraint (SQLite)."""
    if connection.dialect.name != "postgresql":
        constraint_name = _find_crop_id_unique_constraint(connection)
        if constraint_name is None:
            return
        with op.batch_alter_table(
            "ocr_results", naming_convention=_BATCH_NAMING_CONVENTION
        ) as batch_op:
            batch_op.drop_constraint(constraint_name, type_="unique")
        return
    while targets := _find_pg_unique_on_crop_id(connection):
        for name, kind in targets:
            if kind == "constraint":
                op.drop_constraint(name, "ocr_results", type_="unique")
            else:
                op.drop_index(name, table_name="ocr_results")


def _create_crop_id_unique_constraint() -> None:
    connection = op.get_bind()
    if _find_crop_id_unique_constraint(connection) is not None:
        return
    if connection.dialect.name == "sqlite":
        with op.batch_alter_table(
            "ocr_results", naming_convention=_BATCH_NAMING_CONVENTION
        ) as batch_op:
            batch_op.create_unique_constraint("crop_id", ["crop_id"])
        return
    op.create_unique_constraint("crop_id", "ocr_results", ["crop_id"])


def upgrade() -> None:
    op.add_column(
        "ocr_results",
        sa.Column(
            "ocr_index",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    _drop_unique_on_crop_id(op.get_bind())
    op.create_index(
        "idx_ocr_results_crop_index",
        "ocr_results",
        ["crop_id", "ocr_index"],
    )
    _assert_crop_id_not_unique(op.get_bind())


def downgrade() -> None:
    op.drop_index("idx_ocr_results_crop_index", table_name="ocr_results")
    _create_crop_id_unique_constraint()
    op.drop_column("ocr_results", "ocr_index")
