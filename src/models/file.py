from datetime import datetime
from src.models.user import db

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'pdf', 'zip', 'image', etc.
    file_size = db.Column(db.Integer, nullable=False)  # tamanho em bytes
    mime_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
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
