from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from src.models.file import File, ArticleFile
from src.models.article import Article
from src.models.user import db
import os
import uuid
from datetime import datetime

files_bp = Blueprint('files', __name__, url_prefix='/files')

# Extensões permitidas
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'zip': 'application/zip',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload de arquivo
@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    # Verificar se há arquivo na requisição
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado', 'danger')
        return redirect(url_for('files.list_files'))
        
    file = request.files['file']
    
    # Verificar se o arquivo tem nome
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('files.list_files'))
        
    # Verificar se o arquivo é permitido
    if not allowed_file(file.filename):
        flash('Tipo de arquivo não permitido', 'danger')
        return redirect(url_for('files.list_files'))
        
    # Gerar nome seguro para o arquivo
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Salvar arquivo
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Determinar tipo de arquivo
    file_type = ALLOWED_EXTENSIONS[extension]
    
    # Registrar arquivo no banco de dados
    new_file = File(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_type=file_type,
        file_size=os.path.getsize(file_path),
        mime_type=file_type,
        description=request.form.get('description', ''),
        uploaded_by=current_user.id
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
            flash(f'Arquivo "{original_filename}" enviado e associado ao artigo com sucesso!', 'success')
            return redirect(url_for('articles.edit_article', article_id=article_id))
    
    # Se não estiver associado a um artigo, redirecionar para a lista de arquivos
    flash(f'Arquivo "{original_filename}" enviado com sucesso!', 'success')
    return redirect(url_for('files.list_files'))


# Baixar arquivo
@files_bp.route('/<int:file_id>/download')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # Verificar permissões (todos os usuários autenticados podem baixar arquivos)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(
        upload_folder, 
        file.filename, 
        as_attachment=True, 
        download_name=file.original_filename
    )

# Listar arquivos
@files_bp.route('/')
@login_required
def list_files():
    # Apenas administradores e editores podem ver todos os arquivos
    if current_user.is_admin() or current_user.is_editor():
        files = File.query.order_by(File.uploaded_at.desc()).all()
    else:
        # Usuários normais só veem seus próprios arquivos
        files = File.query.filter_by(uploaded_by=current_user.id).order_by(File.uploaded_at.desc()).all()
    
    return render_template('files/list.html', files=files)

# Excluir arquivo
@files_bp.route('/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # Verificar permissões
    if not current_user.is_admin() and file.uploaded_by != current_user.id:
        flash('Você não tem permissão para excluir este arquivo.', 'danger')
        return redirect(url_for('files.list_files'))
    
    # Remover referências em artigos
    ArticleFile.query.filter_by(file_id=file.id).delete()
    
    # Excluir arquivo físico
    try:
        os.remove(file.file_path)
    except:
        flash('Não foi possível excluir o arquivo físico.', 'warning')
    
    # Excluir registro do banco de dados
    db.session.delete(file)
    db.session.commit()
    
    flash('Arquivo excluído com sucesso.', 'success')
    return redirect(url_for('files.list_files'))

# Associar arquivo a artigo
@files_bp.route('/associate', methods=['POST'])
@login_required
def associate_file():
    article_id = request.form.get('article_id')
    file_id = request.form.get('file_id')
    reference_text = request.form.get('reference_text', '')
    
    if not article_id or not file_id:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    article = Article.query.get_or_404(article_id)
    file = File.query.get_or_404(file_id)
    
    # Verificar permissões
    if not article.is_editable_by(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão para editar este artigo'}), 403
    
    # Verificar se já existe associação
    existing = ArticleFile.query.filter_by(article_id=article_id, file_id=file_id).first()
    if existing:
        existing.reference_text = reference_text
        db.session.commit()
        return jsonify({'success': True, 'message': 'Referência atualizada'})
    
    # Criar nova associação
    article_file = ArticleFile(
        article_id=article_id,
        file_id=file_id,
        reference_text=reference_text
    )
    
    db.session.add(article_file)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Arquivo associado com sucesso'})

# Remover associação de arquivo com artigo
@files_bp.route('/disassociate', methods=['POST'])
@login_required
def disassociate_file():
    article_id = request.form.get('article_id')
    file_id = request.form.get('file_id')
    
    if not article_id or not file_id:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    article = Article.query.get_or_404(article_id)
    
    # Verificar permissões
    if not article.is_editable_by(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão para editar este artigo'}), 403
    
    # Remover associação
    ArticleFile.query.filter_by(article_id=article_id, file_id=file_id).delete()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Associação removida com sucesso'})
