# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from src.models.article import Article, ArticleHistory, Category, Tag
from src.models.article_version import ArticleVersion
from src.models.file import File, ArticleFile
from src.models.user import db, User
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

articles_bp = Blueprint('articles', __name__, url_prefix='/articles')


@articles_bp.route('/')
@login_required
def list_articles():
    # Filtros básicos
    status = request.args.get('status', 'homologado')
    include_archived = request.args.get('include_archived', 'false') == 'true'
    category_id = request.args.get('category_id')
    tag_id = request.args.get('tag_id')
    search_query = request.args.get('q', '')

    query = Article.query

    # Aplica filtro de status
    if status:
        if status == 'homologado' and not include_archived:
            query = query.filter(Article.status == 'homologado')
        elif status == 'homologado' and include_archived:
            query = query.filter(Article.status.in_(['homologado', 'arquivado']))
        else:
            query = query.filter(Article.status == status)

    # Filtro de categoria
    if category_id:
        query = query.filter(Article.category_id == category_id)

    # Filtro de tag
    if tag_id:
        query = query.join(Article.tags).filter(Tag.id == tag_id)

    # Busca textual
    if search_query:
        query = query.filter(
            db.or_(
                Article.title.ilike(f'%{search_query}%'),
                Article.content.ilike(f'%{search_query}%')
            )
        )

    # Usuários comuns só veem 'homologado'
    if not current_user.is_editor():
        query = query.filter(Article.status == 'homologado')

    articles = query.order_by(Article.updated_at.desc()).all()
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

    # Permissão de visualização
    if not article.is_viewable_by(current_user):
        flash('Você não tem permissão para visualizar este artigo.', 'danger')
        return redirect(url_for('articles.list_articles'))

    history = ArticleHistory.query.filter_by(article_id=article_id) \
                  .order_by(ArticleHistory.timestamp.desc()).all()
    article_files = ArticleFile.query.filter_by(article_id=article_id).all()

    # Obter lista de editores para o dropdown
    all_users = User.query.all()
    editors = [u for u in all_users if u.is_editor()]

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

        # Validação básica
        if not title or not content or not category_id:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            return render_template('articles/edit.html', categories=categories, tags=tags)

        # Cria a instância de Article
        article = Article(
            title=title,
            content=content,
            category_id=category_id,
            status=status,
            created_by=current_user.id,
            updated_by=current_user.id
        )

        # Associa tags, se houver
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            article.tags = tags

        # Salva artigo (mas sem commitar ainda)
        db.session.add(article)
        db.session.flush()  # para termos article.id

        # 1) Salvar anexos (se vierem arquivos no form)
        # O input name no template deve ser "attachments" e multiple
        for f in request.files.getlist('attachments'):
            if f and f.filename:
                original_filename = secure_filename(f.filename)
                ext = original_filename.rsplit('.', 1)[1].lower()
                generated_name = f"{uuid.uuid4().hex}.{ext}"
                content_blob = f.read()
                size_blob = len(content_blob)
                mime = f.content_type

                new_file = File(
                    filename=generated_name,
                    original_filename=original_filename,
                    file_type=mime,
                    file_size=size_blob,
                    mime_type=mime,
                    description='',
                    uploaded_by=current_user.id,
                    file_content=content_blob,
                    stored_in_db=True
                )
                db.session.add(new_file)
                db.session.flush()

                link = ArticleFile(
                    article_id=article.id,
                    file_id=new_file.id
                )
                db.session.add(link)

        # 2) Histórico de criação
        history = ArticleHistory(
            article_id=article.id,
            user_id=current_user.id,
            action='create',
            new_status=status
        )
        db.session.add(history)

        # 3) Versão inicial
        version = article.save_version(current_user.id)
        history.version_id = version.id

        # Faz commit de tudo
        db.session.commit()

        flash('Artigo criado com sucesso!', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))

    # GET: exibe formulário
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('articles/edit.html', categories=categories, tags=tags)


@articles_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)

    # Permissão de edição
    if not article.is_editable_by(current_user):
        flash('Você não tem permissão para editar este artigo.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article.id))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_ids = request.form.getlist('tags')
        status = request.form.get('status')

        # Validações mínimas
        if not title or not content or not category_id:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            return render_template('articles/edit.html', article=article, categories=categories, tags=tags)

        status_changed = (article.status != status)
        old_status = article.status

        # Atualiza campos
        article.title = title
        article.content = content
        article.category_id = category_id
        article.status = status
        article.updated_by = current_user.id

        # Atualiza tags
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            article.tags = tags
        else:
            article.tags = []

        # Salva novos anexos (se vieram arquivos)
        for f in request.files.getlist('attachments'):
            if f and f.filename:
                original_filename = secure_filename(f.filename)
                ext = original_filename.rsplit('.', 1)[1].lower()
                generated_name = f"{uuid.uuid4().hex}.{ext}"
                content_blob = f.read()
                size_blob = len(content_blob)
                mime = f.content_type

                new_file = File(
                    filename=generated_name,
                    original_filename=original_filename,
                    file_type=mime,
                    file_size=size_blob,
                    mime_type=mime,
                    description='',
                    uploaded_by=current_user.id,
                    file_content=content_blob,
                    stored_in_db=True
                )
                db.session.add(new_file)
                db.session.flush()

                link = ArticleFile(
                    article_id=article.id,
                    file_id=new_file.id
                )
                db.session.add(link)

        # Histórico de update ou mudança de status
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

        # Salva nova versão
        version = article.save_version(current_user.id)
        history.version_id = version.id

        db.session.commit()

        flash('Artigo atualizado com sucesso!', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))

    # GET: exibe formulário preenchido
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('articles/edit.html', article=article, categories=categories, tags=tags)


@articles_bp.route('/<int:article_id>/versions')
@login_required
def list_versions(article_id):
    article = Article.query.get_or_404(article_id)
    if not article.can_view_versions(current_user):
        flash('Você não tem permissão para ver versões anteriores deste artigo.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article.id))

    versions = ArticleVersion.query.filter_by(article_id=article_id) \
                .order_by(ArticleVersion.version_number.desc()).all()

    return render_template('articles/versions.html', article=article, versions=versions)


@articles_bp.route('/<int:article_id>/versions/<int:version_id>')
@login_required
def view_version(article_id, version_id):
    article = Article.query.get_or_404(article_id)
    version = ArticleVersion.query.get_or_404(version_id)

    if version.article_id != article_id:
        abort(404)
    if not article.can_view_versions(current_user):
        flash('Você não tem permissão para ver esta versão.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article.id))

    return render_template('articles/view_version.html', article=article, version=version)


@articles_bp.route('/<int:article_id>/assign', methods=['POST'])
@login_required
def assign_editor(article_id):
    if not current_user.is_admin():
        flash('Apenas administradores podem atribuir editores.', 'danger')
        return redirect(url_for('articles.view_article', article_id=article_id))

    article = Article.query.get_or_404(article_id)
    editor_id = request.form.get('editor_id')

    if editor_id:
        editor = User.query.get(editor_id)
        if not editor or not editor.is_editor():
            flash('Editor inválido selecionado.', 'danger')
            return redirect(url_for('articles.view_article', article_id=article_id))
        article.assigned_editor_id = editor_id
    else:
        article.assigned_editor_id = None

    db.session.commit()
    flash('Editor atribuído com sucesso!', 'success')
    return redirect(url_for('articles.view_article', article_id=article_id))
