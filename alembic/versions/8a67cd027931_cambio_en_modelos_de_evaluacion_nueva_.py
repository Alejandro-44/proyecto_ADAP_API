"""Cambio en modelos de evaluacion, nueva tabla pivote y templates de evaluacion

Revision ID: 8a67cd027931
Revises: bbb3459a9ee5
Create Date: 2024-11-24 15:25:42.977451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8a67cd027931'
down_revision: Union[str, None] = 'bbb3459a9ee5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar restricciones antes de eliminar la tabla `evaluations`
    op.drop_constraint('responses_evaluation_id_fkey', 'responses', type_='foreignkey')
    op.drop_constraint('calculation_results_evaluation_id_fkey', 'calculation_results', type_='foreignkey')

    # Eliminar la tabla `evaluations`
    op.drop_table('evaluations')

    # Modificar `calculation_results` para usar `employee_evaluation_id`
    op.add_column('calculation_results', sa.Column('employee_evaluation_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'calculation_results_employee_evaluation_id_fkey', 
        'calculation_results', 
        'employee_evaluations', 
        ['employee_evaluation_id'], 
        ['id']
    )
    op.drop_column('calculation_results', 'evaluation_id')

    # Modificar `responses` para usar `employee_evaluation_id`
    op.add_column('responses', sa.Column('employee_evaluation_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'responses_employee_evaluation_id_fkey', 
        'responses', 
        'employee_evaluations', 
        ['employee_evaluation_id'], 
        ['id']
    )
    op.drop_column('responses', 'evaluation_id')


def downgrade() -> None:
    # Restaurar `responses` para usar `evaluation_id`
    op.add_column('responses', sa.Column('evaluation_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint('responses_employee_evaluation_id_fkey', 'responses', type_='foreignkey')
    op.create_foreign_key(
        'responses_evaluation_id_fkey', 
        'responses', 
        'evaluations', 
        ['evaluation_id'], 
        ['id']
    )
    op.drop_column('responses', 'employee_evaluation_id')

    # Restaurar `calculation_results` para usar `evaluation_id`
    op.add_column('calculation_results', sa.Column('evaluation_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint('calculation_results_employee_evaluation_id_fkey', 'calculation_results', type_='foreignkey')
    op.create_foreign_key(
        'calculation_results_evaluation_id_fkey', 
        'calculation_results', 
        'evaluations', 
        ['evaluation_id'], 
        ['id']
    )
    op.drop_column('calculation_results', 'employee_evaluation_id')

    # Restaurar la tabla `evaluations`
    op.create_table(
        'evaluations',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('company_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('assigned_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('due_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('completion_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('is_completed', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='evaluations_company_id_fkey'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], name='evaluations_employee_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='evaluations_pkey')
    )
