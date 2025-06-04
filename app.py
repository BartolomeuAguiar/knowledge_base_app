"""
Ponto de entrada para o Flask CLI.
Este arquivo facilita o uso de comandos como 'flask db migrate' sem precisar especificar --app.
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao sys.path para que os imports funcionem corretamente
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Importa a aplicação Flask do módulo principal
from src.main import app

# Configura o Flask-Migrate
from flask_migrate import Migrate
from src.models import db


migrate = Migrate(app, db)

# Não execute o app aqui, apenas exponha a variável 'app' para o Flask CLI
if __name__ == '__main__':
    print("Este arquivo é apenas um ponto de entrada para o Flask CLI.")
    print("Para executar a aplicação, use 'python src/main.py'")
