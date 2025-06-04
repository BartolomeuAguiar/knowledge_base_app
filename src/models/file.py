from datetime import datetime
from src.models.user import db

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=True)  # Caminho opcional, usado quando o arquivo está no sistema de arquivos
    file_type = db.Column(db.String(50), nullable=False)  # 'pdf', 'zip', 'image', etc.
    file_size = db.Column(db.Integer, nullable=False)  # tamanho em bytes
    mime_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Novo campo para armazenar o conteúdo do arquivo diretamente no banco de dados
    file_content = db.Column(db.LargeBinary, nullable=True)
    
    # Flag para indicar se o arquivo está armazenado no banco de dados ou no sistema de arquivos
    stored_in_db = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<File {self.original_filename}>'
    
    @property
    def is_image(self):
        return self.file_type.startswith('image/')
    
    @property
    def is_pdf(self):
        return self.file_type == 'application/pdf'
    
    @property
    def is_zip(self):
        return self.file_type == 'application/zip'
    
    @property
    def storage_location(self):
        """Retorna a localização de armazenamento do arquivo"""
        return "Banco de Dados" if self.stored_in_db else "Sistema de Arquivos"

class ArticleFile(db.Model):
    __tablename__ = 'article_files'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    reference_text = db.Column(db.Text, nullable=True)  # Texto de referência opcional
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    file = db.relationship('File', backref='article_references')
    
    def __repr__(self):
        return f'<ArticleFile {self.id}>'
