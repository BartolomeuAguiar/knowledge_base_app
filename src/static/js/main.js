// main.js

// -------------------------------------------------------------
// Inicializa o editor Summernote com configurações e callbacks
// -------------------------------------------------------------
function initSummernote() {
  // Verifica se o jQuery ($) e o elemento #editor existem na página
  if (typeof $ !== "undefined" && $("#editor").length > 0) {
    $("#editor").summernote({
      height: 300,
      lang: "pt-BR",
      dialogsInBody: true,          // Move o modal do Summernote para dentro do <body>
      disableDragAndDrop: true,     // Desabilita arrastar/soltar para evitar substituição acidental
      callbacks: {
        // Quando o usuário fizer upload de imagens, chama uploadSummernoteImage para cada arquivo
        onImageUpload: function (files) {
          for (let i = 0; i < files.length; i++) {
            uploadSummernoteImage(files[i]);
          }
        }
      }
    });
  }
}

// -------------------------------------------------------------
// Envia a imagem selecionada pelo Summernote para o servidor e
// insere a URL retornada dentro do editor
// -------------------------------------------------------------
function uploadSummernoteImage(file) {
  // Prepara um FormData contendo a chave "file" esperada pelo Flask
  const data = new FormData();
  data.append("file", file);

  // Obtém o ID do artigo a partir do input hidden #article-id (se existir)
  const articleId = document.getElementById("article-id")?.value || "";

  // Faz um POST para a rota /articles/{articleId}/upload-image
  fetch(`/articles/${articleId}/upload-image`, {
    method: "POST",
    body: data
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.url) {
        // Insere a imagem no Summernote usando a URL fornecida pelo servidor
        $("#editor").summernote("insertImage", data.url);
      } else {
        alert("Erro ao enviar imagem.");
      }
    })
    .catch(() => {
      alert("Erro ao enviar imagem.");
    });
}

// -------------------------------------------------------------
// Inicializa o plugin Select2 para as tags, permitindo criação
// de novas tags e seleção múltipla
// -------------------------------------------------------------
function initSelect2() {
  if (typeof $.fn.select2 !== "undefined" && document.querySelector(".select2-tags")) {
    $(".select2-tags").select2({
      tags: true,
      tokenSeparators: [","],
      placeholder: "Selecione ou digite tags..."
    });
  }
}

// -------------------------------------------------------------
// Exibe uma caixa de confirmação genérica antes de ações destrutivas
// -------------------------------------------------------------
function confirmAction(message) {
  return confirm(message || "Tem certeza que deseja realizar esta ação?");
}

// -------------------------------------------------------------
// Adiciona preview do arquivo selecionado no formulário de upload
// -------------------------------------------------------------
function initFileUpload() {
  const fileInput = document.getElementById("file-input");
  const filePreview = document.getElementById("file-preview");
  const fileForm = document.getElementById("file-upload-form");

  if (fileInput && filePreview) {
    fileInput.addEventListener("change", function () {
      filePreview.innerHTML = "";

      if (this.files && this.files.length > 0) {
        const file = this.files[0];
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB

        let icon = "fa-file";
        if (file.type.includes("pdf")) {
          icon = "fa-file-pdf";
        } else if (file.type.includes("zip") || file.type.includes("archive")) {
          icon = "fa-file-archive";
        } else if (file.type.includes("image")) {
          icon = "fa-file-image";
        }

        const preview = document.createElement("div");
        preview.className = "file-item";
        preview.innerHTML = `
          <div class="file-icon">
            <i class="fas ${icon}"></i>
          </div>
          <div class="file-info">
            <div class="file-name">${file.name}</div>
            <div class="file-meta">${fileSize} MB - ${file.type || "Tipo desconhecido"}</div>
          </div>
        `;

        filePreview.appendChild(preview);
      }
    });
  }

  if (fileForm) {
    fileForm.addEventListener("submit", function (e) {
      const fileInputElement = document.getElementById("file-input");
      if (!fileInputElement.files || fileInputElement.files.length === 0) {
        e.preventDefault();
        alert("Por favor, selecione um arquivo para upload.");
      }
    });
  }
}

// -------------------------------------------------------------
// Abre modal de associação de arquivo existente e envia via AJAX
// -------------------------------------------------------------
function initFileAssociation() {
  const associateButtons = document.querySelectorAll(".associate-file-btn");

  associateButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const fileId = this.getAttribute("data-file-id");
      const fileName = this.getAttribute("data-file-name");
      const articleId = document.getElementById("article-id").value;

      // Preenche campos ocultos do formulário de associação
      document.getElementById("association-file-id").value = fileId;
      document.getElementById("association-article-id").value = articleId;
      document.getElementById("association-file-name").textContent = fileName;

      // Abre o modal Bootstrap para associação
      const modal = new bootstrap.Modal(
        document.getElementById("associateFileModal")
      );
      modal.show();
    });
  });

  const associationForm = document.getElementById("file-association-form");
  if (associationForm) {
    associationForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const fileId = document.getElementById("association-file-id").value;
      const articleId = document.getElementById("association-article-id").value;
      const referenceText = document.getElementById("association-reference-text").value;

      const formData = new FormData();
      formData.append("file_id", fileId);
      formData.append("article_id", articleId);
      formData.append("reference_text", referenceText);

      fetch("/files/associate", {
        method: "POST",
        body: formData
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Fecha o modal e recarrega a página para atualizar a tabela
            const modal = bootstrap.Modal.getInstance(
              document.getElementById("associateFileModal")
            );
            modal.hide();
            window.location.reload();
          } else {
            alert("Erro ao associar arquivo: " + data.message);
          }
        })
        .catch((error) => {
          console.error("Erro:", error);
          alert("Erro ao associar arquivo. Por favor, tente novamente.");
        });
    });
  }
}

// -------------------------------------------------------------
// Atualiza a busca de artigos automaticamente ao mudar filtros
// -------------------------------------------------------------
function initArticleSearch() {
  const searchForm = document.getElementById("article-search-form");
  const searchInput = document.getElementById("search-query");
  const categorySelect = document.getElementById("category-filter");
  const tagSelect = document.getElementById("tag-filter");
  const archivedCheckbox = document.getElementById("include-archived");

  if (searchForm) {
    // Quando categorias, tags ou checkbox mudarem, submete o formulário
    [categorySelect, tagSelect, archivedCheckbox].forEach((element) => {
      if (element) {
        element.addEventListener("change", function () {
          searchForm.submit();
        });
      }
    });

    // Debounce para o campo de texto (500ms de intervalo)
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
          searchForm.submit();
        }, 500);
      });
    }
  }
}

// -------------------------------------------------------------
// Função chamada ao clicar em "Desanexar" para remover associação
// -------------------------------------------------------------
function disassociateFile(articleId, fileId, button) {
  if (!confirm("Remover associação deste arquivo?")) return;

  // Caso esteja usando CSRF, capture o token no meta
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");

  fetch("/files/disassociate", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrfToken
    },
    body: new URLSearchParams({
      article_id: articleId,
      file_id: fileId
    })
  })
    .then((response) => {
      if (response.ok) {
        // Remove a linha correspondente da tabela na interface
        const row = button.closest("tr");
        if (row) row.parentNode.removeChild(row);
      } else {
        alert("Erro ao remover associação.");
      }
    })
    .catch((err) => {
      console.error("Erro:", err);
      alert("Erro de conexão ao remover associação.");
    });
}

// ---------------------------------------------------------------------------------
// Bloqueia o foco de Bootstrap Modal sobre o modal interno do Summernote para evitar
// "piscar" incessante quando a caixa de seleção de arquivo aparece.
// ---------------------------------------------------------------------------------
$(document).on("focusin", function (e) {
  if ($(e.target).closest(".note-modal").length) {
    e.stopImmediatePropagation();
  }
});

// -------------------------------------------------------------
// Depois que o DOM é carregado, inicializa todas as funções
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
  initSummernote();
  initSelect2();
  initFileUpload();
  initFileAssociation();
  initArticleSearch();

  // Inicializa tooltips do Bootstrap
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
