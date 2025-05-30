import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus
from datetime import datetime

from flask import Flask, render_template
from flask_login import LoginManager
from werkzeug.utils import secure_filename

# Define base directory (one level above src/)
BASE_DIR = Path(__file__).parent.parent

# Load environment variables from .env in UTF-8
load_dotenv(BASE_DIR / '.env', encoding='utf-8')

# Add project root to sys.path so 'src' package is discoverable
sys.path.insert(0, str(BASE_DIR))

app = Flask(__name__)
# SECRET_KEY from .env or default
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'admin')

# Inject current datetime into all Jinja2 templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Database configuration (escape non-ASCII in password)
db_user     = os.getenv('DB_USERNAME', 'cdf_user_system')
db_password = quote_plus(os.getenv('DB_PASSWORD', 'cdfsystem'))
db_host     = os.getenv('DB_HOST',     'localhost')
db_port     = os.getenv('DB_PORT',     '5432')
db_name     = os.getenv('DB_NAME',     'cdf_db')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{db_user}:{db_password}"
    f"@{db_host}:{db_port}/{db_name}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = str(BASE_DIR / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database and login manager
from src.models import db, init_db
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view    = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

from src.models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from src.routes.auth     import auth_bp
from src.routes.articles import articles_bp
from src.routes.files    import files_bp
from src.routes.admin    import admin_bp
for bp in (auth_bp, articles_bp, files_bp, admin_bp):
    app.register_blueprint(bp)

@app.route('/')
def index():
    return render_template('index.html')

# Create tables if not exist
with app.app_context():
    init_db(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
