# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, MultipleFileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileRequired

class ArticleForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()])
    body = TextAreaField('Conteúdo', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('rascunho', 'Rascunho'),
        ('em_analise', 'Em Análise'),
        ('homologado', 'Homologado'),
        ('arquivado', 'Arquivado'),
    ], default='rascunho')
    # Permite múltiplos arquivos — imagens, pdf, zip, etc.
    attachments = MultipleFileField(
        'Anexos (imagens, PDF, ZIP etc.)',
        validators=[FileAllowed(['jpg','jpeg','png','gif','pdf','zip'], 'Extensão inválida')]
    )
