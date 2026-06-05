"""p4: cadastros básicos (11 tabelas)

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-03
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

CADASTROS = [
    "centro_custo",
    "conta_contabil",
    "cargo",
    "colaborador",
    "fornecedor",
    "combustivel",
    "tipo_equipamento",
    "tipo_servico",
    "grupo_insumo",
    "unidade_medida",
    "insumo",
]


def _op_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    ]


def _rls(table: str) -> None:
    op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])
    op.create_index(
        f"ix_{table}_tenant_created", table, ["tenant_id", sa.text("created_at DESC")]
    )
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.current_tenant', TRUE), '')::uuid)
        """
    )


def _uq_nome(table: str) -> None:
    op.create_index(
        f"uq_{table}_tenant_nome",
        table,
        ["tenant_id", "nome"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def upgrade() -> None:
    op.create_table(
        "centro_custo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("responsavel", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("centro_custo")
    _uq_nome("centro_custo")

    op.create_table(
        "conta_contabil",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("grupo", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("conta_contabil")
    _uq_nome("conta_contabil")

    op.create_table(
        "cargo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("salario", sa.Numeric(15, 4), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("cargo")
    _uq_nome("cargo")

    op.create_table(
        "colaborador",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column(
            "cargo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cargo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("telefone", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("colaborador")
    _uq_nome("colaborador")
    op.create_index("ix_colaborador_cargo_id", "colaborador", ["cargo_id"])

    op.create_table(
        "fornecedor",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=True),
        sa.Column("cnpj_cpf", sa.String(18), nullable=True),
        sa.Column("rg_ie", sa.String(255), nullable=True),
        sa.Column("endereco", sa.String(255), nullable=True),
        sa.Column("bairro", sa.String(255), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("cidade", sa.String(255), nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("telefone", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("fornecedor")
    _uq_nome("fornecedor")

    op.create_table(
        "combustivel",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("combustivel")
    _uq_nome("combustivel")

    op.create_table(
        "tipo_equipamento",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("depreciacao_anual", sa.Numeric(15, 4), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("tipo_equipamento")
    _uq_nome("tipo_equipamento")

    op.create_table(
        "tipo_servico",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("tipo_servico")
    _uq_nome("tipo_servico")

    op.create_table(
        "grupo_insumo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("grupo_insumo")
    _uq_nome("grupo_insumo")

    op.create_table(
        "unidade_medida",
        *_op_columns(),
        sa.Column("codigo", sa.String(5), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("unidade_medida")
    op.create_index(
        "uq_unidade_medida_tenant_codigo",
        "unidade_medida",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "insumo",
        *_op_columns(),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column(
            "grupo_insumo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("grupo_insumo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "unidade_medida_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade_medida.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("preco_medio", sa.Numeric(15, 4), nullable=True),
        sa.Column("marca", sa.String(255), nullable=True),
        sa.Column("fabricante", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    _rls("insumo")
    _uq_nome("insumo")
    op.create_index("ix_insumo_grupo_insumo_id", "insumo", ["grupo_insumo_id"])
    op.create_index("ix_insumo_unidade_medida_id", "insumo", ["unidade_medida_id"])


def downgrade() -> None:
    for table in reversed(CADASTROS):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.drop_table(table)
