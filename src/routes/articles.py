from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from src.models.article import Article, Category, Tag, ArticleHistory, article_tags
from src.models.file import File, ArticleFile
from src.models.user import User, db
import os
import uuid
from datetime import datetime

articles_bp = Blueprint('articles', __name__, url_prefix='/articles')

# Função auxiliar para verificar permissões
def check_article_permission(article_id, edit=False):
    article = Article.query.get_or_404(article_id)
    
    if edit:
        if not article.is_editable_by(current_user):
            flash('Você não tem permissão para editar este artigo.', 'danger')
            return None
    else:
        if not article.is_viewable_by(current_user):
            flash('Você não tem permissão para visualizar este artigo.', 'danger')
            return None
            
    return article

# Listar artigos
@articles_bp.route('/')
@login_required
def list_articles():
    # Parâmetros de busca e filtro
    search_query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    tag_id = request.args.get('tag', '')
    include_archived = request.args.get('archived', '') == 'true'
    
    # Consulta base
    query = Article.query
    
    # Filtrar por status
    if current_user.is_admin() or current_user.is_editor():
        # Admins e editores podem ver todos os status, exceto arquivados se não solicitado
        if not include_archived:
            query = query.filter(Article.status != 'arquivado')
    else:
        # Usuários normais só veem homologados, e arquivados se solicitado
        if include_archived:
            query = query.filter(Article.status.in_(['homologado', 'arquivado']))
        else:
            query = query.filter_by(status='homologado')
    
    # Aplicar filtros de busca
    if search_query:
        query = query.filter(
            (Article.title.ilike(f'%{search_query}%')) | 
            (Article.content.ilike(f'%{search_query}%'))
        )
    
    # Filtrar por categoria
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Filtrar por tag
    if tag_id:
        query = query.join(Article.tags).filter(Tag.id == tag_id)
    
    # Ordenar por data de atualização
    articles = query.order_by(Article.updated_at.desc()).all()
    
    # Obter categorias e tags para os filtros
    categories = Category.query.all()
    tags = Tag.query.all()
    
    return render_template(
        'articles/list.html', 
        articles=articles, 
        categories=categories, 
        tags=tags,
        search_query=search_query,
        category_id=category_id,
        tag_id=tag_id,
        include_archived=include_archived
    )

# Visualizar artigo
@articles_bp.route('/<int:article_id>')
@login_required
def view_article(article_id):
    article = check_article_permission(article_id)
    if not article:
        return redirect(url_for('articles.list_articles'))
    
    return render_template('articles/view.html', article=article)

# Criar novo artigo
@articles_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_article():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_names = request.form.getlist('tags')
        
        # Validar dados
        if not title or not content:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            return render_template('articles/edit.html', categories=categories, tags=tags)
        
        # Verificar categoria
        if not category_id:
            # Usar categoria geral se não for especificada
            category = Category.query.filter_by(name='Geral').first()
            category_id = category.id
        
        # Criar artigo
        article = Article(
            title=title,
            content=content,
            status='rascunho',
            created_by=current_user.id,
            updated_by=current_user.id,
            category_id=category_id
        )
        
        # Adicionar tags
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            article.tags.append(tag)
        
        db.session.add(article)
        
        # Registrar histórico
        history = ArticleHistory(
            article=article,
            user_id=current_user.id,
            action='create',
            new_status='rascunho'
        )
        db.session.add(history)
        
        db.session.commit()
        
        flash('Artigo criado com sucesso.', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))
    
    # GET - Exibir formulário
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('articles/edit.html', categories=categories, tags=tags)

# Editar artigo
@articles_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = check_article_permission(article_id, edit=True)
    
    if not article:
        return redirect(url_for('articles.list_articles'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_names = request.form.getlist('tags')
        
        # Validar dados
        if not title or not content:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            files = File.query.order_by(File.created_at.desc()).all()
            return render_template(
                'articles/edit.html',
                article=article,
                categories=categories,
                tags=tags,
                files=files
            )
        
        # Atualizar artigo
        article.title = title
        article.content = content
        article.category_id = category_id
        article.updated_by = current_user.id
        
        # Atualizar tags
        article.tags = []
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            article.tags.append(tag)
        
        # Registrar histórico
        history = ArticleHistory(
            article=article,
            user_id=current_user.id,
            action='update'
        )
        db.session.add(history)
        
        db.session.commit()
        
        flash('Artigo atualizado com sucesso.', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))
    
    # GET - Exibir formulário
    categories = Category.query.all()
    tags = Tag.query.all()
    files = File.query.order_by(File.uploaded_at.desc()).all()
    
    return render_template(
        'articles/edit.html',
        article=article,
        categories=categories,
        tags=tags,
        files=files
    )



# Alterar status do artigo
@articles_bp.route('/<int:article_id>/status', methods=['POST'])
@login_required
def change_status(article_id):
    article = check_article_permission(article_id, edit=True)
    if not article:
        return redirect(url_for('articles.list_articles'))
    
    new_status = request.form.get('status')
    if new_status not in ['rascunho', 'em_analise', 'homologado', 'arquivado']:
        flash('Status inválido.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article.id))
    
    old_status = article.status
    article.status = new_status
    article.updated_by = current_user.id
    
    # Registrar histórico
    history = ArticleHistory(
        article=article,
        user_id=current_user.id,
        action='status_change',
        old_status=old_status,
        new_status=new_status
    )
    db.session.add(history)
    
    db.session.commit()
    
    flash(f'Status do artigo alterado para {new_status}.', 'success')
    return redirect(url_for('articles.view_article', article_id=article.id))

# Excluir artigo
@articles_bp.route('/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    if not current_user.is_admin():
        flash('Apenas administradores podem excluir artigos.', 'danger')
        return redirect(url_for('articles.list_articles'))
    
    article = Article.query.get_or_404(article_id)
    
    # Excluir histórico
    ArticleHistory.query.filter_by(article_id=article.id).delete()
    
    # Excluir referências a arquivos
    ArticleFile.query.filter_by(article_id=article.id).delete()
    
    # Excluir artigo
    db.session.delete(article)
    db.session.commit()
    
    flash('Artigo excluído com sucesso.', 'success')
    return redirect(url_for('articles.list_articles'))

@articles_bp.route('/<int:article_id>/upload-image', methods=['POST'])
@login_required
def upload_article_image(article_id):
    article = check_article_permission(article_id, edit=True)
    if not article:
        return jsonify({'error': 'Sem permissão'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Arquivo não encontrado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo inválido'}), 400

    from werkzeug.utils import secure_filename
    import os
    import uuid

    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'articles', str(article_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{file_id}_{filename}")
    file.save(file_path)

    file_url = url_for('static', filename=f'uploads/articles/{article_id}/{file_id}_{filename}', _external=True)
    return jsonify({'url': file_url})

