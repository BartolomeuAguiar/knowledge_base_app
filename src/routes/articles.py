from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify, send_file
from flask_login import login_required, current_user
from src.models.article import Article, ArticleHistory, Category, Tag
from src.models.article_version import ArticleVersion
from src.models.file import File, ArticleFile
from src.models.user import db, User
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import io
import tempfile
from weasyprint import HTML, CSS

articles_bp = Blueprint('articles', __name__, url_prefix='/articles')

@articles_bp.route('/')
@login_required
def list_articles():
    # Filtrar por status
    status = request.args.get('status', 'homologado')
    include_archived = request.args.get('archived', 'false') == 'true'
    
    # Filtrar por categoria
    category_id = request.args.get('category')
    
    # Filtrar por tag
    tag_id = request.args.get('tag')
    
    # Busca por texto
    search_query = request.args.get('q', '')
    
    # Construir a query base
    query = Article.query
    
    # Aplicar filtros
    if status:
        if status == 'homologado' and not include_archived:
            query = query.filter(Article.status == 'homologado')
        elif status == 'homologado' and include_archived:
            query = query.filter(Article.status.in_(['homologado', 'arquivado']))
        else:
            query = query.filter(Article.status == status)
    
    # Filtrar por categoria
    if category_id:
        query = query.filter(Article.category_id == category_id)
    
    # Filtrar por tag
    if tag_id:
        query = query.join(Article.tags).filter(Tag.id == tag_id)
    
    # Busca por texto
    if search_query:
        query = query.filter(
            db.or_(
                Article.title.ilike(f'%{search_query}%'),
                Article.content.ilike(f'%{search_query}%')
            )
        )
    
    # Usuários normais só veem artigos homologados
    if not current_user.is_editor():
        query = query.filter(Article.status == 'homologado')
    
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
        status=status,
        include_archived=include_archived,
        category_id=category_id,
        tag_id=tag_id,
        search_query=search_query
    )

@articles_bp.route('/<int:article_id>')
@login_required
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # Verificar permissão
    if not article.is_viewable_by(current_user):
        flash('Você não tem permissão para visualizar este artigo.', 'danger')
        return redirect(url_for('articles.list_articles'))
    
    # Obter histórico
    history = ArticleHistory.query.filter_by(article_id=article_id).order_by(ArticleHistory.timestamp.desc()).all()
    
    # Obter arquivos associados
    article_files = ArticleFile.query.filter_by(article_id=article_id).all()
    
    # Obter editores para atribuição (apenas para admins)
    editors = []
    if current_user.is_admin():
        editors = User.query.filter(User.role.in_(['admin', 'editor'])).all()
    
    return render_template(
        'articles/view.html',
        article=article,
        history=history,
        article_files=article_files,
        editors=editors
    )

@articles_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_article():
    if not current_user.is_editor():
        flash('Você não tem permissão para criar artigos.', 'danger')
        return redirect(url_for('articles.list_articles'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_ids = request.form.getlist('tags')
        status = request.form.get('status', 'rascunho')
        
        # Validar dados
        if not title or not content or not category_id:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            return render_template('articles/edit.html', categories=categories, tags=tags)
        
        # Criar artigo
        article = Article(
            title=title,
            content=content,
            category_id=category_id,
            status=status,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        # Adicionar tags
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            article.tags = tags
        
        db.session.add(article)
        db.session.commit()
        
        # Registrar histórico
        history = ArticleHistory(
            article_id=article.id,
            user_id=current_user.id,
            action='create',
            new_status=status
        )
        db.session.add(history)
        
        # Salvar versão inicial
        version = article.save_version(current_user.id)
        history.version_id = version.id
        db.session.commit()
        
        flash('Artigo criado com sucesso!', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))
    
    # GET: Exibir formulário
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('articles/edit.html', categories=categories, tags=tags)

@articles_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # Verificar permissão
    if not article.is_editable_by(current_user):
        flash('Você não tem permissão para editar este artigo.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_ids = request.form.getlist('tags')
        status = request.form.get('status') or 'rascunho'
        
        # Validar dados
        if not title or not content or not category_id:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            return render_template('articles/edit.html', article=article, categories=categories, tags=tags)
        
        # Verificar se houve mudança de status
        status_changed = article.status != status
        old_status = article.status
        
        # Atualizar artigo
        article.title = title
        article.content = content
        article.category_id = category_id
        article.status = status
        article.updated_by = current_user.id
        
        # Atualizar tags
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            article.tags = tags
        else:
            article.tags = []
        
        # Registrar histórico
        if status_changed:
            action = 'status_change'
        else:
            action = 'update'
        
        history = ArticleHistory(
            article_id=article.id,
            user_id=current_user.id,
            action=action,
            old_status=old_status if status_changed else None,
            new_status=status if status_changed else None
        )
        db.session.add(history)
        
        # Salvar nova versão
        version = article.save_version(current_user.id)
        history.version_id = version.id
        db.session.commit()
        
        flash('Artigo atualizado com sucesso!', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))
    
    # GET: Exibir formulário
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('articles/edit.html', article=article, categories=categories, tags=tags)

@articles_bp.route('/<int:article_id>/versions')
@login_required
def list_versions(article_id):
    article = Article.query.get_or_404(article_id)
    
    # Verificar permissão
    if not article.can_view_versions(current_user):
        flash('Você não tem permissão para visualizar versões anteriores deste artigo.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article_id))
    
    # Obter todas as versões
    versions = ArticleVersion.query.filter_by(article_id=article_id).order_by(ArticleVersion.version_number.desc()).all()
    
    return render_template(
        'articles/versions.html',
        article=article,
        versions=versions
    )

@articles_bp.route('/<int:article_id>/versions/<int:version_id>')
@login_required
def view_version(article_id, version_id):
    article = Article.query.get_or_404(article_id)
    version = ArticleVersion.query.get_or_404(version_id)
    
    # Verificar se a versão pertence ao artigo
    if version.article_id != article_id:
        abort(404)
    
    # Verificar permissão
    if not article.can_view_versions(current_user):
        flash('Você não tem permissão para visualizar versões anteriores deste artigo.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article_id))
    
    return render_template(
        'articles/view_version.html',
        article=article,
        version=version
    )

@articles_bp.route('/<int:article_id>/assign', methods=['POST'])
@login_required
def assign_editor(article_id):
    if not current_user.is_admin():
        flash('Você não tem permissão para atribuir editores.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article_id))
    
    article = Article.query.get_or_404(article_id)
    editor_id = request.form.get('editor_id')
    
    if editor_id:
        editor = User.query.get(editor_id)
        if not editor or not editor.is_editor():
            flash('Editor inválido.', 'danger')
            return redirect(url_for('articles.view_article', article_id=article_id))
        
        article.assigned_editor_id = editor_id
        flash(f'Editor atribuído com sucesso.', 'success')
    else:
        article.assigned_editor_id = None
        flash('Atribuição de editor removida.', 'success')
    
    db.session.commit()
    return redirect(url_for('articles.view_article', article_id=article_id))

@articles_bp.route('/<int:article_id>/pdf')
@login_required
def generate_pdf(article_id):
    article = Article.query.get_or_404(article_id)
    
    # Verificar permissão
    if not article.is_viewable_by(current_user):
        flash('Você não tem permissão para visualizar este artigo.', 'danger')
        return redirect(url_for('articles.list_articles'))
    
    # Preparar dados para o template
    user_name = current_user.full_name or current_user.username
    generated_at = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Renderizar o template HTML
    html_content = render_template(
        'articles/article_pdf.html',
        article=article,
        user_name=user_name,
        generated_at=generated_at
    )
    
    # Criar arquivo PDF temporário
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        # Gerar PDF com WeasyPrint
        HTML(string=html_content).write_pdf(
            temp_file.name,
            stylesheets=[
                CSS(string='@page { size: A4; margin: 1cm }')
            ]
        )
        temp_file_path = temp_file.name
    
    # Enviar o arquivo PDF como resposta
    return send_file(
        temp_file_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{article.title.replace(' ', '_')}.pdf",
        # Após o envio, o arquivo temporário será excluído
        max_age=0
    )
