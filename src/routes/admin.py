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
    total_tags = Tag.query.count()
    
    # Artigos por status
    articles_by_status = db.session.query(
        Article.status, db.func.count(Article.id)
    ).group_by(Article.status).all()
    
    status_data = {status: count for status, count in articles_by_status}
    
    # Artigos recentes
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_articles=total_articles,
        total_categories=total_categories,
        total_tags=total_tags,
        status_data=json.dumps(status_data),
        recent_articles=recent_articles
    )

# Gerenciar usuários
@admin_bp.route('/users')
@login_required
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Criar usuário
@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if request.method == 'POST':
        # Captura do formulário
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', '').strip()
        active = True if request.form.get('active') == 'on' else False
        password = request.form.get('password', '').strip()

        # 1) Validações iniciais
        if not username:
            flash('O nome de usuário é obrigatório.', 'danger')
            return render_template('admin/create_user.html', form=request.form)
        if ' ' in username:
            flash('O nome de usuário não pode conter espaços.', 'danger')
            return render_template('admin/create_user.html', form=request.form)

        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'danger')
            return render_template('admin/create_user.html', form=request.form)

        if not email:
            flash('O e-mail é obrigatório.', 'danger')
            return render_template('admin/create_user.html', form=request.form)
        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está em uso.', 'danger')
            return render_template('admin/create_user.html', form=request.form)

        if not password:
            flash('A senha é obrigatória para criar um novo usuário.', 'danger')
            return render_template('admin/create_user.html', form=request.form)

        # 2) Criação do objeto User
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            active=active
        )
        new_user.set_password(password)

        # 3) Commit
        db.session.add(new_user)
        db.session.commit()

        flash('Usuário criado com sucesso.', 'success')
        return redirect(url_for('admin.list_users'))

    # GET: exibe o formulário em branco
    return render_template('admin/create_user.html')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    # 1) Garantir que user_id seja um inteiro válido. Se não existir, abort 404.
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # Captura dos dados vindos do form
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', '').strip()
        active = True if request.form.get('active') == 'on' else False
        password = request.form.get('password', '').strip()

        ### 2) VALIDAÇÕES ###

        # 2.1) Username não pode ser vazio
        if not username:
            flash('O nome de usuário não pode ficar vazio.', 'danger')
            return render_template('admin/edit_user.html', user=user)

        # 2.2) Username não pode conter espaços
        if ' ' in username:
            flash('O nome de usuário não pode conter espaços.', 'danger')
            return render_template('admin/edit_user.html', user=user)

        # 2.3) Se estiver alterando o username, checar unicidade
        if username != user.username:
            other = User.query.filter_by(username=username).first()
            if other:
                flash('Este nome de usuário já está em uso.', 'danger')
                return render_template('admin/edit_user.html', user=user)

        # 2.4) Se estiver alterando o e-mail, checar unicidade
        if email != user.email:
            other_email = User.query.filter_by(email=email).first()
            if other_email:
                flash('Este e-mail já está em uso.', 'danger')
                return render_template('admin/edit_user.html', user=user)

        # Não exigimos que o usuário digite a senha obrigatoriamente. Se vier em branco, mantém a anterior.
        # Se quiser alterar a senha, digite algo em password; caso contrário, ignore.

        ### 3) SE PASSOU NAS VALIDAÇÕES, atualizar os campos ###
        user.username = username
        user.email = email
        user.full_name = full_name
        user.role = role
        user.active = active

        if password:
            user.set_password(password)
            flash('Senha atualizada.', 'info')
        # Senão: mantém o password_hash atual

        db.session.commit()
        flash('Informações do usuário atualizadas com sucesso.', 'success')
        return redirect(url_for('admin.list_users'))

    # ===========================
    # Método GET: simplesmente carrega o formulário
    # ===========================
    # Neste ponto, 'user' já contém todos os dados atuais: username, email, full_name, role, active.
    # A senha NÃO será “enviada” ao template (ficará em branco por padrão), para o usuário digitar apenas se for alterar.
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

# Criar categoria
@admin_bp.route('/categories/create', methods=['POST'])
@login_required
def create_category():
    name = request.form.get('name')
    description = request.form.get('description')
    parent_id = request.form.get('parent_id') or None
    
    # Validar dados
    if not name:
        flash('Nome da categoria é obrigatório.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    # Verificar se o nome já existe
    existing = Category.query.filter_by(name=name).first()
    if existing:
        flash('Nome de categoria já existe.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    # Criar categoria
    category = Category(
        name=name,
        description=description,
        parent_id=parent_id
    )
    
    db.session.add(category)
    db.session.commit()
    
    flash('Categoria criada com sucesso.', 'success')
    return redirect(url_for('admin.list_categories'))

# Atualizar categoria
@admin_bp.route('/categories/update', methods=['POST'])
@login_required
def update_category():
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    description = request.form.get('description')
    parent_id = request.form.get('parent_id') or None
    
    category = Category.query.get_or_404(category_id)
    
    # Validar dados
    if not name:
        flash('Nome da categoria é obrigatório.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    # Verificar se o nome já existe
    existing = Category.query.filter_by(name=name).first()
    if existing and existing.id != int(category_id):
        flash('Nome de categoria já existe.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    # Verificar ciclo de referência
    if parent_id and int(parent_id) == category.id:
        flash('Uma categoria não pode ser pai dela mesma.', 'danger')
        return redirect(url_for('admin.list_categories'))
    
    # Atualizar categoria
    category.name = name
    category.description = description
    category.parent_id = parent_id
    
    db.session.commit()
    flash('Categoria atualizada com sucesso.', 'success')
    return redirect(url_for('admin.list_categories'))

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

# Criar tag
@admin_bp.route('/tags/create', methods=['POST'])
@login_required
def create_tag():
    name = request.form.get('name')
    
    # Validar dados
    if not name:
        flash('Nome da tag é obrigatório.', 'danger')
        return redirect(url_for('admin.list_tags'))
    
    # Verificar se o nome já existe
    existing = Tag.query.filter_by(name=name).first()
    if existing:
        flash('Nome de tag já existe.', 'danger')
        return redirect(url_for('admin.list_tags'))
    
    # Criar tag
    tag = Tag(name=name)
    
    db.session.add(tag)
    db.session.commit()
    
    flash('Tag criada com sucesso.', 'success')
    return redirect(url_for('admin.list_tags'))

# Atualizar tag
@admin_bp.route('/tags/update', methods=['POST'])
@login_required
def update_tag():
    tag_id = request.form.get('tag_id')
    name = request.form.get('name')
    
    tag = Tag.query.get_or_404(tag_id)
    
    # Validar dados
    if not name:
        flash('Nome da tag é obrigatório.', 'danger')
        return redirect(url_for('admin.list_tags'))
    
    # Verificar se o nome já existe
    existing = Tag.query.filter_by(name=name).first()
    if existing and existing.id != int(tag_id):
        flash('Nome de tag já existe.', 'danger')
        return redirect(url_for('admin.list_tags'))
    
    # Atualizar tag
    tag.name = name
    
    db.session.commit()
    flash('Tag atualizada com sucesso.', 'success')
    return redirect(url_for('admin.list_tags'))

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

# Gerenciar artigos pendentes
@admin_bp.route('/articles')
@login_required
def list_pending_articles():
    draft_articles = Article.query.filter_by(status='rascunho').order_by(Article.updated_at.desc()).all()
    review_articles = Article.query.filter_by(status='em_analise').order_by(Article.updated_at.desc()).all()
    approved_articles = Article.query.filter_by(status='homologado').order_by(Article.updated_at.desc()).all()
    archived_articles = Article.query.filter_by(status='arquivado').order_by(Article.updated_at.desc()).all()
    
    return render_template(
        'admin/articles.html',
        draft_articles=draft_articles,
        review_articles=review_articles,
        approved_articles=approved_articles,
        archived_articles=archived_articles
    )

# Alterar status de artigo
@admin_bp.route('/articles/change-status', methods=['POST'])
@login_required
def change_article_status():
    article_id = request.form.get('article_id')
    status = request.form.get('status')
    
    article = Article.query.get_or_404(article_id)
    
    # Validar status
    valid_statuses = ['rascunho', 'em_analise', 'homologado', 'arquivado']
    if status not in valid_statuses:
        flash('Status inválido.', 'danger')
        return redirect(url_for('admin.list_pending_articles'))
    
    # Atualizar status
    article.status = status
    article.last_updated_by = current_user.id
    
    db.session.commit()
    
    status_names = {
        'rascunho': 'Rascunho',
        'em_analise': 'Em Análise',
        'homologado': 'Homologado',
        'arquivado': 'Arquivado'
    }
    
    flash(f'Artigo "{article.title}" alterado para {status_names.get(status, status)}.', 'success')
    return redirect(url_for('admin.list_pending_articles'))
