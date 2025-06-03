from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from src.models.article import Article, Category, Tag, ArticleHistory, article_tags
from src.models.file import File, ArticleFile
from src.models.user import User, db
import os
import io
import uuid
from datetime import datetime
from xhtml2pdf import pisa

articles_bp = Blueprint('articles', __name__, url_prefix='/articles')

# Função auxiliar para verificar permissões de visualização/edição


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
    search_query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    tag_id = request.args.get('tag', '')
    include_archived = request.args.get('archived', '') == 'true'

    query = Article.query

    if current_user.is_admin() or current_user.is_editor():
        if not include_archived:
            query = query.filter(Article.status != 'arquivado')
    else:
        if include_archived:
            query = query.filter(Article.status.in_(
                ['homologado', 'arquivado']))
        else:
            query = query.filter_by(status='homologado')

    if search_query:
        query = query.filter(
            (Article.title.ilike(f'%{search_query}%')) |
            (Article.content.ilike(f'%{search_query}%'))
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    if tag_id:
        query = query.join(Article.tags).filter(Tag.id == tag_id)

    articles = query.order_by(Article.updated_at.desc()).all()
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

    # Verifica de novo (usado no template para mostrar ou não o botão “Editar”)
    can_edit = article.is_editable_by(current_user)
    return render_template('articles/view.html', article=article, can_edit=can_edit)

# Criar novo artigo


@articles_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_article():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_names = request.form.getlist('tags')

        if not title or not content:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            return render_template('articles/edit.html', categories=categories, tags=tags)

        if not category_id:
            categoria_geral = Category.query.filter_by(name='Geral').first()
            category_id = categoria_geral.id

        article = Article(
            title=title,
            content=content,
            status='rascunho',
            created_by=current_user.id,
            updated_by=current_user.id,
            category_id=category_id
            # assigned_editor_id ficará None por padrão
        )

        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            article.tags.append(tag)

        db.session.add(article)

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

    # Lista todos os usuários com role='editor' (para o dropdown que só admin verá)
    editors = User.query.filter_by(role='editor').all()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        tag_names = request.form.getlist('tags')

        if not title or not content:
            flash('Título e conteúdo são obrigatórios.', 'danger')
            categories = Category.query.all()
            tags = Tag.query.all()
            files = File.query.order_by(File.uploaded_at.desc()).all()
            return render_template(
                'articles/edit.html',
                article=article,
                categories=categories,
                tags=tags,
                files=files,
                editors=editors  # repassa mesmo em erro para re-renderizar dropdown, se admin
            )

        # Atualiza campos básicos
        article.title = title
        article.content = content
        article.category_id = category_id
        article.updated_by = current_user.id

        # Atualiza tags
        article.tags = []
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            article.tags.append(tag)

        # Se o usuário logado for ADMIN, processa o assigned_editor_id
        if current_user.is_admin():
            assigned_id = request.form.get('assigned_editor_id')
            if assigned_id:
                # Se veio algo e corresponde a um editor válido
                try:
                    assigned_id_int = int(assigned_id)
                    user_assigned = User.query.get(assigned_id_int)
                    if user_assigned and user_assigned.role == 'editor':
                        article.assigned_editor_id = assigned_id_int
                    else:
                        # Se for inválido (não existe ou não é editor), desempacha
                        article.assigned_editor_id = None
                    # Observação: se quiser permitir “desatribuir”, basta enviar campo vazio
                except ValueError:
                    article.assigned_editor_id = None
            else:
                # Campo vazio → remover atribuição
                article.assigned_editor_id = None

        # Histórico de atualização
        history = ArticleHistory(
            article=article,
            user_id=current_user.id,
            action='update'
        )
        db.session.add(history)

        db.session.commit()

        flash('Artigo atualizado com sucesso.', 'success')
        return redirect(url_for('articles.view_article', article_id=article.id))

    # GET: exibe formulário de edição
    categories = Category.query.all()
    tags = Tag.query.all()
    files = File.query.order_by(File.uploaded_at.desc()).all()

    return render_template(
        'articles/edit.html',
        article=article,
        categories=categories,
        tags=tags,
        files=files,
        # lista de editores para exibir no dropdown (apenas para admins)
        editors=editors
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

# Excluir artigo (apenas admin)


@articles_bp.route('/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    if not current_user.is_admin():
        flash('Apenas administradores podem excluir artigos.', 'danger')
        return redirect(url_for('articles.list_articles'))

    article = Article.query.get_or_404(article_id)

    # Excluir histórico
    ArticleHistory.query.filter_by(article_id=article.id).delete()

    # Excluir arquivos vinculados
    ArticleFile.query.filter_by(article_id=article.id).delete()

    # Excluir artigo em si
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

    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    upload_dir = os.path.join(
        current_app.static_folder, 'uploads', 'articles', str(article_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{file_id}_{filename}")
    file.save(file_path)

    file_url = url_for(
        'static', filename=f'uploads/articles/{article_id}/{file_id}_{filename}', _external=True)
    return jsonify({'url': file_url})


@articles_bp.route('/<int:article_id>/export_pdf', methods=['GET'])
@login_required
def export_article_pdf(article_id):
    """
    Gera um PDF do artigo via xhtml2pdf, incorporando imagens em
    src/static/uploads/articles/<article_id>/…,
    adicionando marca d’água e rodapé.
    """
    # 1) Busca o artigo
    artigo = Article.query.get_or_404(article_id)

    # 2) Dados para o rodapé
    user_name = current_user.username
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # 3) Renderiza o HTML-base (com marca d’água e rodapé em <div>)
    html_out = render_template(
        'articles/article_pdf.html',
        article=artigo,
        user_name=user_name,
        generated_at=generated_at
    )

    # 4) Converte HTML em PDF usando BytesIO
    pdf_buffer = io.BytesIO()
    result = pisa.CreatePDF(
        src=html_out,
        dest=pdf_buffer,
        link_callback=_link_callback
    )

    # 5) Se houver erro na geração, retorna 500
    if result.err:
        return f"Erro ao gerar PDF: {result.err}", 500

    # 6) Retorna o PDF como download
    pdf_bytes = pdf_buffer.getvalue()
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"artigo_{artigo.id}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def _link_callback(uri, rel):
    """
    Converte as URIs em caminhos absolutos. Se detectar recurso externo (http:// ou https://),
    devolve string vazia para forçar pisa a ignorar a referência, evitando timeouts.
    """
    # 1) Se for URL absoluta (http:// ou https://), devolve vazio (ignora)
    if uri.startswith('http://') or uri.startswith('https://'):
        return ""  # força pisa a não tentar baixar via HTTPS

    # 2) Se começar com '/', mapeia para "<root_path>/static/..."
    if uri.startswith('/'):
        base_path = current_app.root_path  # ex: .../knowledge_base_app/src
        sub_path = uri.lstrip('/').replace('/', os.path.sep)
        full_path = os.path.join(base_path, sub_path)
        if os.path.isfile(full_path):
            return full_path

        # Se quiser mapear também uploads fora de src, descomente e ajuste:
        # base_project = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
        # alt_path = os.path.join(base_project, sub_path)
        # if os.path.isfile(alt_path):
        #     return alt_path

    # 3) Qualquer outro caso, retorna string vazia para ignorar
    return ""
