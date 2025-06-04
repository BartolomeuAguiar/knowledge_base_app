from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

# instância única do SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'editor', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    #articles_created = db.relationship('Article', backref='creator', lazy=True, foreign_keys='Article.created_by')
    #articles_updated = db.relationship('Article', backref='updater', lazy=True, foreign_keys='Article.updated_by')
    #files_uploaded = db.relationship('File', backref='uploader', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_editor(self):
        return self.role == 'editor' or self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def is_active(self):
        # UserMixin also provides default is_active, but override to use 'active' flag
        return self.active
