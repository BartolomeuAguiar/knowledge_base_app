// Scripts personalizados para o dashboard administrativo

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Configurar modais de edição
    setupEditModals();
    
    // Configurar validação de formulários
    setupFormValidation();
    
    // Configurar animações de cards
    setupCardAnimations();
});

// Configurar modais de edição
function setupEditModals() {
    // Modal de edição de usuário
    const editUserModal = document.getElementById('editUserModal');
    if (editUserModal) {
        editUserModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const userId = button.getAttribute('data-user-id');
            const username = button.getAttribute('data-username');
            const email = button.getAttribute('data-email');
            const fullName = button.getAttribute('data-fullname');
            const role = button.getAttribute('data-role');
            const active = button.getAttribute('data-active') === '1';
            
            const modal = this;
            modal.querySelector('#edit-user-id').value = userId;
            modal.querySelector('#edit-username').value = username;
            modal.querySelector('#edit-email').value = email;
            modal.querySelector('#edit-full-name').value = fullName;
            modal.querySelector('#edit-role').value = role;
            modal.querySelector('#edit-active').checked = active;
            modal.querySelector('#reset-password').checked = false;
        });
    }
    
    // Modal de edição de categoria
    const editCategoryModal = document.getElementById('editCategoryModal');
    if (editCategoryModal) {
        editCategoryModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const categoryId = button.getAttribute('data-category-id');
            const name = button.getAttribute('data-name');
            const description = button.getAttribute('data-description');
            const parentId = button.getAttribute('data-parent-id');
            
            const modal = this;
            modal.querySelector('#edit-category-id').value = categoryId;
            modal.querySelector('#edit-category-name').value = name;
            modal.querySelector('#edit-category-description').value = description;
            
            const parentSelect = modal.querySelector('#edit-category-parent');
            if (parentSelect) {
                // Remover a própria categoria das opções de categoria pai
                Array.from(parentSelect.options).forEach(option => {
                    if (option.value === categoryId) {
                        option.disabled = true;
                    } else {
                        option.disabled = false;
                    }
                });
                
                parentSelect.value = parentId;
            }
        });
    }
    
    // Modal de edição de tag
    const editTagModal = document.getElementById('editTagModal');
    if (editTagModal) {
        editTagModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const tagId = button.getAttribute('data-tag-id');
            const name = button.getAttribute('data-name');
            
            const modal = this;
            modal.querySelector('#edit-tag-id').value = tagId;
            modal.querySelector('#edit-tag-name').value = name;
        });
    }
}

// Configurar validação de formulários
function setupFormValidation() {
    // Validação de formulário de novo usuário
    const newUserForm = document.getElementById('new-user-form');
    if (newUserForm) {
        newUserForm.addEventListener('submit', function(event) {
            const password = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('new-confirm-password').value;
            
            if (password !== confirmPassword) {
                event.preventDefault();
                alert('As senhas não coincidem.');
            }
        });
    }
}

// Configurar animações de cards
function setupCardAnimations() {
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    dashboardCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
        });
    });
}

// Função para confirmar ações
function confirmAction(message) {
    return confirm(message || 'Tem certeza que deseja realizar esta ação?');
}

// Função para alterar status de artigo
function changeArticleStatus(articleId, newStatus) {
    if (confirmAction(`Tem certeza que deseja alterar o status deste artigo para "${getStatusName(newStatus)}"?`)) {
        const form = document.getElementById('change-status-form');
        document.getElementById('article-id').value = articleId;
        document.getElementById('new-status').value = newStatus;
        form.submit();
    }
}

// Função para obter nome legível do status
function getStatusName(status) {
    switch(status) {
        case 'rascunho': return 'Rascunho';
        case 'em_analise': return 'Em Análise';
        case 'homologado': return 'Homologado';
        case 'arquivado': return 'Arquivado';
        default: return status;
    }
}
