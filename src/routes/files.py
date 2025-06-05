from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
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
    """Download de arquivo"""
    file = File.query.get_or_404(file_id)
    
    # Se o arquivo está armazenado no banco de dados
    if file.stored_in_db and file.file_content:
        # Criar um objeto BytesIO a partir do conteúdo binário
        file_data = io.BytesIO(file.file_content)
        
        # Enviar o arquivo como resposta
        return send_file(
            file_data,
            mimetype=file.mime_type,
            as_attachment=True,
            download_name=file.original_filename
        )
    
    # Se o arquivo está no sistema de arquivos
    elif file.file_path and os.path.exists(file.file_path):
        return send_file(
            file.file_path,
            mimetype=file.mime_type,
            as_attachment=True,
            download_name=file.original_filename
        )
    
    # Arquivo não encontrado
    else:
        flash('Arquivo não encontrado.', 'danger')
        return redirect(url_for('files.list_files'))

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload de arquivo"""
    # Verificar se há arquivo na requisição
    if 'file' not in request.files:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'})
        flash('Nenhum arquivo enviado', 'danger')
        return redirect(url_for('files.list_files'))
        
    file = request.files['file']
    
    # Verificar se o arquivo tem nome
    if file.filename == '':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'})
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('files.list_files'))
        
    # Verificar se o arquivo é permitido
    if not allowed_file(file.filename):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Tipo de arquivo não permitido'})
        flash('Tipo de arquivo não permitido', 'danger')
        return redirect(url_for('files.list_files'))
        
    # Gerar nome seguro para o arquivo
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Determinar tipo de arquivo
    file_type = file.content_type
    
    # Ler o conteúdo do arquivo
    file_content = file.read()
    file_size = len(file_content)
    
    # Criar registro no banco de dados
    new_file = File(
        filename=filename,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        mime_type=file.content_type,
        description=request.form.get('description', ''),
        uploaded_by=current_user.id,
        file_content=file_content,  # Armazenar conteúdo no banco
        stored_in_db=True  # Marcar como armazenado no banco
    )
    
    db.session.add(new_file)
    db.session.commit()
    
    # Verificar se o upload está associado a um artigo
    article_id = request.form.get('article_id')
    if article_id:
        article = Article.query.get(article_id)
        if article and article.is_editable_by(current_user):
            article_file = ArticleFile(
                article_id=article_id,
                file_id=new_file.id,
                reference_text=request.form.get('reference_text', '')
            )
            db.session.add(article_file)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'file_id': new_file.id,
                    'filename': original_filename,
                    'file_type': file_type
                })
            
            flash(f'Arquivo "{original_filename}" enviado e associado ao artigo com sucesso!', 'success')
            return redirect(url_for('articles.edit_article', article_id=article_id))
    
    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'file_id': new_file.id,
            'filename': original_filename,
            'file_type': file_type
        })
    
    # Se não estiver associado a um artigo, redirecionar para a lista de arquivos
    flash(f'Arquivo "{original_filename}" enviado com sucesso!', 'success')
    return redirect(url_for('files.list_files'))

@files_bp.route('/serve/<int:file_id>')
def serve_file(file_id):
    """Serve um arquivo para visualização no navegador (não como download)"""
    file = File.query.get_or_404(file_id)
    
    # Se o arquivo está armazenado no banco de dados
    if file.stored_in_db and file.file_content:
        # Criar um objeto BytesIO a partir do conteúdo binário
        file_data = io.BytesIO(file.file_content)
        
        # Enviar o arquivo como resposta
        return send_file(
            file_data,
            mimetype=file.mime_type,
            as_attachment=False
        )
    
    # Se o arquivo está no sistema de arquivos
    elif file.file_path and os.path.exists(file.file_path):
        return send_file(
            file.file_path,
            mimetype=file.mime_type,
            as_attachment=False
        )
    
    # Arquivo não encontrado
    else:
        abort(404)

@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Exclui um arquivo"""
    file = File.query.get_or_404(file_id)
    
    # Verificar permissão (apenas admin ou quem enviou)
    if not current_user.is_admin() and file.uploaded_by != current_user.id:
        flash('Você não tem permissão para excluir este arquivo.', 'danger')
        return redirect(url_for('files.list_files'))
    
    # Remover associações com artigos
    ArticleFile.query.filter_by(file_id=file_id).delete()
    
    # Se o arquivo estiver no sistema de arquivos, excluí-lo
    if not file.stored_in_db and file.file_path and os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Excluir registro do banco
    db.session.delete(file)
    db.session.commit()
    
    flash('Arquivo excluído com sucesso!', 'success')
    return redirect(url_for('files.list_files'))
