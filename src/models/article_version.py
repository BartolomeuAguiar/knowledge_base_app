from datetime import datetime
from src.models.user import db

class ArticleVersion(db.Model):
    """
    Modelo para armazenar versões completas de artigos.
    Cada vez que um artigo é atualizado, uma nova versão é criada.
    """
    __tablename__ = 'article_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relacionamentos
    article = db.relationship('Article', backref='versions')
    creator = db.relationship('User', backref='article_versions')
    
    def __repr__(self):
        return f'<ArticleVersion {self.article_id}-v{self.version_number}>'
    
    @classmethod
    def create_from_article(cls, article, user_id):
        """
        Cria uma nova versão a partir de um artigo existente.
        
        Args:
            article: Objeto Article do qual criar uma versão
            user_id: ID do usuário que está criando a versão
            
        Returns:
            Nova instância de ArticleVersion
        """
        # Encontrar o número da próxima versão
        last_version = cls.query.filter_by(article_id=article.id).order_by(
            cls.version_number.desc()).first()
        
        next_version = 1
        if last_version:
            next_version = last_version.version_number + 1
            
        # Criar nova versão
        version = cls(
            article_id=article.id,
            version_number=next_version,
            title=article.title,
            content=article.content,
            status=article.status,
            created_by=user_id
        )
        
        return version
