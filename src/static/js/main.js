// Scripts personalizados para a Base de Conhecimento TIC

// Inicialização do TinyMCE para o editor de artigos
function initTinyMCE() {
    if (typeof tinymce !== 'undefined' && document.querySelector('#editor')) {
        tinymce.init({
            selector: '#editor',
            height: 500,
            menubar: true,
            plugins: [
                'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                'insertdatetime', 'media', 'table', 'help', 'wordcount'
            ],
            toolbar: 'undo redo | formatselect | ' +
                'bold italic backcolor | alignleft aligncenter ' +
                'alignright alignjustify | bullist numlist outdent indent | ' +
                'removeformat | image | help',
            content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; }',
            images_upload_handler: function (blobInfo, success, failure) {
                var xhr, formData;
                xhr = new XMLHttpRequest();
                xhr.withCredentials = false;
                xhr.open('POST', '/files/upload');
                
                xhr.onload = function() {
                    var json;
                    
                    if (xhr.status != 200) {
                        failure('Erro ao fazer upload da imagem: ' + xhr.status);
                        return;
                    }
                    
                    json = JSON.parse(xhr.responseText);
                    
                    if (!json || !json.success) {
                        failure('Erro ao fazer upload da imagem: ' + (json && json.message ? json.message : 'Erro desconhecido'));
                        return;
                    }
                    
                    success('/files/' + json.file_id + '/download');
                };
                
                formData = new FormData();
                formData.append('file', blobInfo.blob(), blobInfo.filename());
                
                xhr.send(formData);
            }
        });
    }
}

// Inicialização do Select2 para seleção de tags
function initSelect2() {
    if (typeof $.fn.select2 !== 'undefined' && document.querySelector('.select2-tags')) {
        $('.select2-tags').select2({
            tags: true,
            tokenSeparators: [','],
            placeholder: 'Selecione ou digite tags...'
        });
    }
}

// Confirmação para ações destrutivas
function confirmAction(message) {
    return confirm(message || 'Tem certeza que deseja realizar esta ação?');
}

// Upload de arquivos com preview
function initFileUpload() {
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const fileForm = document.getElementById('file-upload-form');
    
    if (fileInput && filePreview) {
        fileInput.addEventListener('change', function() {
            filePreview.innerHTML = '';
            
            if (this.files && this.files.length > 0) {
                const file = this.files[0];
                const fileSize = (file.size / 1024 / 1024).toFixed(2); // em MB
                
                let icon = 'fa-file';
                if (file.type.includes('pdf')) {
                    icon = 'fa-file-pdf';
                } else if (file.type.includes('zip') || file.type.includes('archive')) {
                    icon = 'fa-file-archive';
                } else if (file.type.includes('image')) {
                    icon = 'fa-file-image';
                }
                
                const preview = document.createElement('div');
                preview.className = 'file-item';
                preview.innerHTML = `
                    <div class="file-icon">
                        <i class="fas ${icon}"></i>
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-meta">${fileSize} MB - ${file.type || 'Tipo desconhecido'}</div>
                    </div>
                `;
                
                filePreview.appendChild(preview);
            }
        });
    }
    
    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('file-input');
            if (!fileInput.files || fileInput.files.length === 0) {
                e.preventDefault();
                alert('Por favor, selecione um arquivo para upload.');
            }
        });
    }
}

// Associação de arquivos a artigos
function initFileAssociation() {
    const associateButtons = document.querySelectorAll('.associate-file-btn');
    
    associateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-file-id');
            const fileName = this.getAttribute('data-file-name');
            const articleId = document.getElementById('article-id').value;
            
            // Preencher o modal com as informações do arquivo
            document.getElementById('association-file-id').value = fileId;
            document.getElementById('association-article-id').value = articleId;
            document.getElementById('association-file-name').textContent = fileName;
            
            // Abrir o modal
            const modal = new bootstrap.Modal(document.getElementById('associateFileModal'));
            modal.show();
        });
    });
    
    // Formulário de associação
    const associationForm = document.getElementById('file-association-form');
    if (associationForm) {
        associationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileId = document.getElementById('association-file-id').value;
            const articleId = document.getElementById('association-article-id').value;
            const referenceText = document.getElementById('association-reference-text').value;
            
            const formData = new FormData();
            formData.append('file_id', fileId);
            formData.append('article_id', articleId);
            formData.append('reference_text', referenceText);
            
            fetch('/files/associate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fechar o modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('associateFileModal'));
                    modal.hide();
                    
                    // Recarregar a página para mostrar a associação
                    window.location.reload();
                } else {
                    alert('Erro ao associar arquivo: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao associar arquivo. Por favor, tente novamente.');
            });
        });
    }
}

// Busca dinâmica de artigos
function initArticleSearch() {
    const searchForm = document.getElementById('article-search-form');
    const searchInput = document.getElementById('search-query');
    const categorySelect = document.getElementById('category-filter');
    const tagSelect = document.getElementById('tag-filter');
    const archivedCheckbox = document.getElementById('include-archived');
    
    if (searchForm) {
        // Atualizar a busca quando os filtros mudarem
        [categorySelect, tagSelect, archivedCheckbox].forEach(element => {
            if (element) {
                element.addEventListener('change', function() {
                    searchForm.submit();
                });
            }
        });
        
        // Busca com debounce para o campo de texto
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function() {
                    searchForm.submit();
                }, 500);
            });
        }
    }
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    initTinyMCE();
    initSelect2();
    initFileUpload();
    initFileAssociation();
    initArticleSearch();
    
    // Tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
