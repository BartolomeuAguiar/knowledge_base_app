# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.models.user import db, User

class File(db.Model):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)              # nome interno gerado (UUID + extensão)
    original_filename = Column(String(255), nullable=False)     # nome original do arquivo
    file_path = Column(String(512), nullable=True)              # caminho no disco (caso armazenado em FS)
    file_type = Column(String(50), nullable=False)              # ex: 'application/pdf', 'image/png', etc.
    file_size = Column(Integer, nullable=False)                 # tamanho em bytes
    mime_type = Column(String(100), nullable=False)             # mesmo que file_type, mas pra clareza
    description = Column(Text, nullable=True)                   # descrição opcional
    uploaded_at = Column(DateTime, default=datetime.utcnow)     # timestamp de upload
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)  # quem enviou

    # Novo campo: conteúdo binário (BLOB) do arquivo
    file_content = Column(LargeBinary, nullable=True)

    # Flag para saber onde está armazenado (banco de dados ou sistema de arquivos)
    stored_in_db = Column(Boolean, default=False)

    # Relacionamentos
    uploader = relationship('User', foreign_keys=[uploaded_by], backref='files_uploaded')

    def __repr__(self):
        return f'<File {self.original_filename}>'

    @property
    def is_image(self):
        return self.mime_type.startswith('image/')

    @property
    def is_pdf(self):
        return self.mime_type == 'application/pdf'

    @property
    def is_zip(self):
        return self.mime_type == 'application/zip'

    @property
    def storage_location(self):
        return "Banco de Dados" if self.stored_in_db else "Sistema de Arquivos"


class ArticleFile(db.Model):
    __tablename__ = 'article_files'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    reference_text = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamento para navegar do ArticleFile → File
    file = relationship('File', backref='article_references')

    def __repr__(self):
        return f'<ArticleFile {self.id}>'
