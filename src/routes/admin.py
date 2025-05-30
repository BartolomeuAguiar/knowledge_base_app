from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from src.models.user import User, db
from src.models.article import Category, Tag, Article
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Verificar se o usuário é administrador
@admin_bp.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('index'))

# Dashboard administrativo
@admin_bp.route('/')
@login_required
def dashboard():
    # Estatísticas
    total_users = User.query.count()
    total_articles = Article.query.count()
    total_categories = Category.query.count()
    
    # Artigos por status
    articles_by_status = db.session.query(
        Article.status, db.func.count(Article.id)
    ).group_by(Article.status).all()
    
    status_data = {status: count for status, count in articles_by_status}
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_articles=total_articles,
        total_categories=total_categories,
        status_data=json.dumps(status_data)
    )

# Gerenciar usuários
@admin_bp.route('/users')
@login_required
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Editar usuário
@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        active = 'active' in request.form
        
        # Verificar se o username já existe
        if username != user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Nome de usuário já está em uso.', 'danger')
                return render_template('admin/edit_user.html', user=user)
        
        # Verificar se o email já existe
        if email != user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email já está em uso.', 'danger')
                return render_template('admin/edit_user.html', user=user)
        
        # Atualizar usuário
        user.username = username
        user.email = email
        user.full_name = full_name
        user.role = role
        user.active = active
        
        # Resetar senha se solicitado
        if 'reset_password' in request.form:
            user.set_password('password123')  # Senha temporária
            flash('Senha resetada para: password123', 'warning')
        
        db.session.commit()
        flash('Usuário atualizado com sucesso.', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('admin/edit_user.html', user=user)

# Excluir usuário
@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Não permitir excluir o próprio usuário
    if user.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('admin.list_users'))
    
    # Excluir usuário
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário excluído com sucesso.', 'success')
    return redirect(url_for('admin.list_users'))

# Gerenciar categorias
@admin_bp.route('/categories')
@login_required
def list_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

# Criar/Editar categoria
@admin_bp.route('/categories/edit', methods=['GET', 'POST'])
@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id=None):
    if category_id:
        category = Category.query.get_or_404(category_id)
    else:
        category = None
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id') or None
        
        # Validar dados
        if not name:
            flash('Nome da categoria é obrigatório.', 'danger')
            categories = Category.query.all()
            return render_template('admin/edit_category.html', category=category, categories=categories)
        
        # Verificar se o nome já existe
        existing = Category.query.filter_by(name=name).first()
        if existing and (not category or existing.id != category.id):
            flash('Nome de categoria já existe.', 'danger')
            categories = Category.query.all()
            return render_template('admin/edit_category.html', category=category, categories=categories)
        
        # Criar ou atualizar categoria
        if not category:
            category = Category(name=name, description=description, parent_id=parent_id)
            db.session.add(category)
            flash('Categoria criada com sucesso.', 'success')
        else:
            category.name = name
            category.description = description
            category.parent_id = parent_id
            flash('Categoria atualizada com sucesso.', 'success')
        
        db.session.commit()
        return redirect(url_for('admin.list_categories'))
    
    categories = Category.query.all()
    return render_template('admin/edit_category.html', category=category, categories=categories)

# Excluir categoria
@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Verificar se é a categoria geral
    if category.name == 'Geral':
        flash('A categoria Geral não pode ser excluída.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    # Verificar se há artigos associados
    if category.articles:
        # Mover artigos para a categoria geral
        geral = Category.query.filter_by(name='Geral').first()
        for article in category.articles:
            article.category_id = geral.id
    
    # Verificar se há subcategorias
    if category.subcategories:
        # Mover subcategorias para o nível superior
        for subcategory in category.subcategories:
            subcategory.parent_id = category.parent_id
    
    # Excluir categoria
    db.session.delete(category)
    db.session.commit()
    
    flash('Categoria excluída com sucesso.', 'success')
    return redirect(url_for('admin.list_categories'))

# Gerenciar tags
@admin_bp.route('/tags')
@login_required
def list_tags():
    tags = Tag.query.all()
    return render_template('admin/tags.html', tags=tags)

# Excluir tag
@admin_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    # Excluir tag
    db.session.delete(tag)
    db.session.commit()
    
    flash('Tag excluída com sucesso.', 'success')
    return redirect(url_for('admin.list_tags'))
