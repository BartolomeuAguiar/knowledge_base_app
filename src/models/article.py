from datetime import datetime
from src.models.user import db, User  # adicionamos a importação de User para o relacionamento

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    articles = db.relationship('Article', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Tabela de associação entre artigos e tags
article_tags = db.Table('article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='rascunho')  # 'rascunho', 'em_analise', 'homologado', 'arquivado'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Autor (quem criou)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Última atualização
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # NOVO: campo “editor designado” (opcional)
    assigned_editor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relacionamentos
    tags = db.relationship('Tag', secondary=article_tags, backref=db.backref('articles', lazy='dynamic'))
    files = db.relationship('ArticleFile', backref='article', lazy=True)
    history = db.relationship('ArticleHistory', backref='article', lazy=True)
    
    # Relacionamento para o editor designado
    assigned_editor = db.relationship('User', foreign_keys=[assigned_editor_id], backref='articles_assigned')

    def __repr__(self):
        return f'<Article {self.title}>'
    
    def is_viewable_by(self, user):
        """Verifica se o usuário pode visualizar o artigo."""
        if user.is_admin() or user.is_editor():
            return True
        return self.status == 'homologado'
    
    def is_editable_by(self, user):
        """
        Verifica se o usuário pode editar o artigo:
         - Administradores podem editar sempre.
         - Editores (role='editor') podem editar somente se:
             • forem quem criou (created_by) OU
             • forem o assigned_editor deste artigo.
        """
        if user.is_admin():
            return True

        # Se for editor regular (ou super‐editor), precisa ser autor ou designado
        if user.is_editor():
            if user.id == self.created_by:
                return True
            if self.assigned_editor_id is not None and user.id == self.assigned_editor_id:
                return True
        
        return False

class ArticleHistory(db.Model):
    __tablename__ = 'article_history'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'status_change'
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='article_actions')
    
    def __repr__(self):
        return f'<ArticleHistory {self.action} on {self.article_id}>'
