from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        # Verificar se o usuário existe e a senha está correta
        if not user or not user.check_password(password):
            flash('Usuário ou senha incorretos. Por favor, tente novamente.', 'danger')
            return render_template('auth/login.html')
            
        # Verificar se o usuário está ativo
        if not user.active:
            flash('Sua conta está desativada. Entre em contato com o administrador.', 'warning')
            return render_template('auth/login.html')
            
        # Fazer login do usuário
        login_user(user, remember=remember)
        
        # Atualizar data do último login
        user.last_login = db.func.now()
        db.session.commit()
        
        # Redirecionar para a página solicitada ou para a página inicial
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Verificar se o registro está aberto ou se apenas administradores podem registrar usuários
    # Neste caso, apenas administradores podem registrar novos usuários
    if current_user.is_authenticated and not current_user.is_admin():
        flash('Apenas administradores podem registrar novos usuários.', 'warning')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Verificar se as senhas coincidem
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/register.html')
            
        # Verificar se o usuário já existe
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Nome de usuário já está em uso.', 'danger')
            return render_template('auth/register.html')
            
        # Verificar se o email já existe
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email já está em uso.', 'danger')
            return render_template('auth/register.html')
            
        # Criar novo usuário
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='user',  # Papel padrão
            active=True
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro realizado com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Atualizar informações básicas
        current_user.full_name = full_name
        
        # Verificar se o email está sendo alterado
        if email != current_user.email:
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email já está em uso.', 'danger')
                return render_template('auth/profile.html')
            current_user.email = email
            
        # Verificar se a senha está sendo alterada
        if current_password and new_password and confirm_password:
            if not current_user.check_password(current_password):
                flash('Senha atual incorreta.', 'danger')
                return render_template('auth/profile.html')
                
            if new_password != confirm_password:
                flash('As novas senhas não coincidem.', 'danger')
                return render_template('auth/profile.html')
                
            current_user.set_password(new_password)
            flash('Senha alterada com sucesso.', 'success')
            
        db.session.commit()
        flash('Perfil atualizado com sucesso.', 'success')
        
    return render_template('auth/profile.html')
