from src.models.user import db, User
from src.models.article import Category, Tag, Article, ArticleHistory
from src.models.file import File, ArticleFile

# Função para inicializar o banco de dados
def init_db(app):
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        
        # Verificar se já existe um usuário administrador
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Criar usuário administrador padrão
            admin = User(
                username='admin',
                email='admin@example.com',
                full_name='Administrador',
                role='admin',
                active=True
            )
            admin.set_password('admin123')  # Senha temporária que deve ser alterada
            db.session.add(admin)
            
            # Criar categoria geral padrão
            general_category = Category(
                name='Geral',
                description='Categoria geral para artigos não categorizados'
            )
            db.session.add(general_category)
            
            db.session.commit()
            
        return True
