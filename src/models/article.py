# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from src.models.user import db, User
from src.models.article_version import ArticleVersion

# -------------------------------------------------------------------------
# Categoria


class Category(db.Model):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship('Category', remote_side=[
                          id], backref='subcategories')
    articles = relationship('Article', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


# Tabela associativa Article ↔ Tag
article_tags = db.Table(
    'article_tags',
    db.metadata,   # <<< aqui é FUNDAMENTAL passar db.metadata como segundo argumento
    db.Column('article_id', db.Integer, db.ForeignKey(
        'articles.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


# -------------------------------------------------------------------------
# Tag
class Tag(db.Model):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<Tag {self.name}>'


# -------------------------------------------------------------------------
# Modelo principal: Article
class Article(db.Model):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    # rascunho / em_analise / homologado / arquivado
    status = Column(String(20), nullable=False, default='rascunho')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Autor e quem atualizou
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Categoria obrigatória
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    # Editor designado (opcional)
    assigned_editor_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relacionamentos
    tags = relationship('Tag', secondary=article_tags,
                        backref=db.backref('articles', lazy='dynamic'))
    files = relationship('ArticleFile', backref='article', lazy=True)
    history = relationship('ArticleHistory', backref='article', lazy=True)

    # Relacionamentos para usuário
    creator = db.relationship('User', foreign_keys=[created_by], backref='articles_created')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='articles_updated')
    assigned_editor = db.relationship('User', foreign_keys=[assigned_editor_id], backref='articles_assigned')

    def __repr__(self):
        return f'<Article {self.title}>'

    def is_viewable_by(self, user):
        """Quem pode ver: admin/editor sempre; usuários normais só veem 'homologado'."""
        if user.is_admin() or user.is_editor():
            return True
        return self.status == 'homologado'

    def is_editable_by(self, user):
        """
        Verifica permissão de edição:
         - Admin: sempre
         - Editor: se for autor (created_by) ou se for assigned_editor
        """
        if user.is_admin():
            return True
        if user.is_editor():
            if user.id == self.created_by:
                return True
            if self.assigned_editor_id is not None and user.id == self.assigned_editor_id:
                return True
        return False

    def can_view_versions(self, user):
        """Somente admin/editor podem ver histórico de versões."""
        return user.is_admin() or user.is_editor()

    def save_version(self, user_id):
        """
        Cria uma nova ArticleVersion com base no estado atual deste artigo.
        Retorna a instância criada (mas não faz commit).
        """
        version = ArticleVersion.create_from_article(self, user_id)
        db.session.add(version)
        return version


# -------------------------------------------------------------------------
# Histórico de alterações (status, update, create)
class ArticleHistory(db.Model):
    __tablename__ = 'article_history'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(50), nullable=False)     # 'create' / 'update' / 'status_change'
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version_id = Column(Integer, ForeignKey('article_versions.id'), nullable=True)

    # Relacionamentos
    user = relationship('User', backref='article_actions')
    version = relationship('ArticleVersion', backref='history_entries')

    def __repr__(self):
        return f'<ArticleHistory {self.action} on {self.article_id}>'
