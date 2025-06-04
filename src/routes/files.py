# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import io
from src.models.file import File, ArticleFile
from src.models.article import Article
from src.models.user import db

files_bp = Blueprint('files', __name__, url_prefix='/files')

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    ALLOWED_EXTENSIONS = {'pdf', 'zip', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@files_bp.route('/')
@login_required
def list_files():
    """Lista todos os arquivos"""
    files = File.query.order_by(File.uploaded_at.desc()).all()
    return render_template('files/list.html', files=files)


@files_bp.route('/<int:file_id>')
@login_required
def download_file(file_id):
    """Faz download do arquivo (attachment)"""
    file = File.query.get_or_404(file_id)

    # Se está no banco, retorna o blob
    if file.stored_in_db and file.file_content:
        buffer = io.BytesIO(file.file_content)
        return send_file(
            buffer,
            mimetype=file.mime_type,
            as_attachment=True,
            download_name=file.original_filename
        )

    # Se está no sistema de arquivos
    elif file.file_path and os.path.exists(file.file_path):
        return send_file(
            file.file_path,
            mimetype=file.mime_type,
            as_attachment=True,
            download_name=file.original_filename
        )

    # Não encontrado
    flash('Arquivo não encontrado.', 'danger')
    return redirect(url_for('files.list_files'))


@files_bp.route('/serve/<int:file_id>')
def serve_file(file_id):
    """
    Retorna o arquivo para exibição inline (não como attachment). 
    Útil para exibir imagens diretamente no navegador.
    """
    file = File.query.get_or_404(file_id)

    if file.stored_in_db and file.file_content:
        buffer = io.BytesIO(file.file_content)
        return send_file(
            buffer,
            mimetype=file.mime_type,
            as_attachment=False
        )
    elif file.file_path and os.path.exists(file.file_path):
        return send_file(
            file.file_path,
            mimetype=file.mime_type,
            as_attachment=False
        )
    else:
        abort(404)


@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Rota de upload genérica. 
    Se vier 'article_id' no form, associa o arquivo ao artigo.
    Retorna JSON em caso de AJAX (por exemplo, uso no Summernote).
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo enviado.'})

    f = request.files['file']
    if f.filename == '':
        return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado.'})

    if not allowed_file(f.filename):
        return jsonify({'success': False, 'error': 'Tipo de arquivo não permitido.'})

    # Gera nome seguro
    original_filename = secure_filename(f.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    generated_name = f"{uuid.uuid4().hex}.{extension}"

    file_content = f.read()
    file_size = len(file_content)
    mime_type = f.content_type

    new_file = File(
        filename=generated_name,
        original_filename=original_filename,
        file_type=mime_type,
        file_size=file_size,
        mime_type=mime_type,
        description=request.form.get('description', ''),
        uploaded_by=current_user.id,
        file_content=file_content,
        stored_in_db=True
    )

    db.session.add(new_file)
    db.session.commit()

    # Se vier article_id, associa ao artigo
    article_id = request.form.get('article_id')
    if article_id:
        article = Article.query.get(article_id)
        if article and article.is_editable_by(current_user):
            link = ArticleFile(
                article_id=article_id,
                file_id=new_file.id,
                reference_text=request.form.get('reference_text', '')
            )
            db.session.add(link)
            db.session.commit()
            flash(f'Arquivo "{original_filename}" enviado e associado ao artigo com sucesso!', 'success')
            return redirect(url_for('articles.edit_article', article_id=article_id))

    # Caso contrário, redireciona à lista de arquivos
    flash(f'Arquivo "{original_filename}" enviado com sucesso!', 'success')
    return redirect(url_for('files.list_files'))


@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Exclui um arquivo (apaga do banco e/ou sistema de arquivos e remove associações)"""
    file = File.query.get_or_404(file_id)

    # Somente admin ou quem enviou pode excluir
    if not current_user.is_admin() and file.uploaded_by != current_user.id:
        flash('Você não tem permissão para excluir este arquivo.', 'danger')
        return redirect(url_for('files.list_files'))

    # Primeiro, remove associações em ArticleFile
    ArticleFile.query.filter_by(file_id=file_id).delete()

    # Se estiver no sistema de arquivos, apaga o arquivo físico
    if not file.stored_in_db and file.file_path and os.path.exists(file.file_path):
        os.remove(file.file_path)

    # Apaga o registro
    db.session.delete(file)
    db.session.commit()

    flash('Arquivo excluído com sucesso!', 'success')
    return redirect(url_for('files.list_files'))
