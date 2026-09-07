"""Initial schema for analyses, detector_results, and evidences tables.

Revision ID: eaca4f4bdcbc
Revises: 
Create Date: 2026-09-07 11:28:46.922231

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'eaca4f4bdcbc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('input_type', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('fraud_types', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('extracted_content', sa.JSON(), nullable=False),
        sa.Column('processing_time_ms', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_analyses_created_at', 'analyses', ['created_at'])

    # 2. Create detector_results table
    op.create_table(
        'detector_results',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('analysis_id', sa.String(), sa.ForeignKey('analyses.id', ondelete='CASCADE'), index=True),
        sa.Column('module', sa.String(), nullable=False),
        sa.Column('fraud_probability', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('risk', sa.String(), nullable=False),
        sa.Column('signals', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('processing_time_ms', sa.Float(), nullable=False),
        sa.Column('metadata_', sa.JSON(), nullable=False),
    )

    # 3. Create evidences table
    op.create_table(
        'evidences',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('analysis_id', sa.String(), sa.ForeignKey('analyses.id', ondelete='CASCADE'), index=True),
        sa.Column('evidence_type', sa.String(), nullable=False),
        sa.Column('source_modality', sa.String(), nullable=False),
        sa.Column('target_modality', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('evidence_relationship', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('evidences')
    op.drop_table('detector_results')
    op.drop_index('ix_analyses_created_at', table_name='analyses')
    op.drop_table('analyses')
