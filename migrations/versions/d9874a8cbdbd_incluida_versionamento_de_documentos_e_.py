"""incluida versionamento de documentos e salvar os arquivos no BD

Revision ID: d9874a8cbdbd
Revises: da1de88d8ac2
Create Date: 2025-06-04 11:41:56.451227

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9874a8cbdbd'
down_revision = 'da1de88d8ac2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('article_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'article_versions', ['version_id'], ['id'])

    with op.batch_alter_table('files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_content', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('stored_in_db', sa.Boolean(), nullable=True))
        batch_op.alter_column('file_path',
               existing_type=sa.VARCHAR(length=512),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('files', schema=None) as batch_op:
        batch_op.alter_column('file_path',
               existing_type=sa.VARCHAR(length=512),
               nullable=False)
        batch_op.drop_column('stored_in_db')
        batch_op.drop_column('file_content')

    with op.batch_alter_table('article_history', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('version_id')

    # ### end Alembic commands ###
