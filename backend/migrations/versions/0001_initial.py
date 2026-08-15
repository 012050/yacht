"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('username', sa.String(20), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('nickname', sa.String(20), nullable=False, unique=True),
        sa.Column('total_games', sa.Integer(), default=0),
        sa.Column('total_wins', sa.Integer(), default=0),
        sa.Column('cumulative_score', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'games',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('host_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('join_code', sa.String(6), nullable=False, unique=True),
        sa.Column('status', sa.String(), nullable=False, server_default='WAITING'),
        sa.Column('current_player_index', sa.Integer(), default=0),
        sa.Column('current_round', sa.Integer(), default=1),
        sa.Column('turn_time_limit', sa.Integer(), default=60),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'game_players',
        sa.Column('game_id', sa.String(), sa.ForeignKey('games.id'), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('join_order', sa.Integer(), nullable=False),
    )

    op.create_table(
        'scoreboards',
        sa.Column('game_id', sa.String(), sa.ForeignKey('games.id'), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('category', sa.String(), primary_key=True),
        sa.Column('score', sa.Integer(), nullable=False),
    )

    op.create_table(
        'game_results',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('game_id', sa.String(), sa.ForeignKey('games.id'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('top_section_sum', sa.Integer(), nullable=False),
        sa.Column('bottom_section_sum', sa.Integer(), nullable=False),
        sa.Column('bonus', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('game_results')
    op.drop_table('scoreboards')
    op.drop_table('game_players')
    op.drop_table('games')
    op.drop_table('users')
