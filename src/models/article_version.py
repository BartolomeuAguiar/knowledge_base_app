from datetime import datetime
from src.models.user import db

class ArticleVersion(db.Model):
    __tablename__ = 'article_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    article = db.relationship('Article', back_populates='versions')
    category = db.relationship('Category')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<ArticleVersion {self.id} - v{self.version_number}>'


    @classmethod
    def create_from_article(cls, article, user_id):
        """
        Cria uma nova versão com base no artigo atual.
        """
        # Determinar o próximo número de versão
        next_version = 1
        if article.versions:
            next_version = max([v.version_number for v in article.versions]) + 1

        return cls(
            article_id=article.id,
            version_number=next_version,
            title=article.title,
            content=article.content,
            status=article.status,
            category_id=article.category_id,
            created_by=user_id
        )