// -------------------------------------------------------------
// disassociate-file.js
// Executa fetch para desassociar arquivo sem recarregar página
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  // Ativa somente se houver botões de desassociação na página
  const disassociateButtons = document.querySelectorAll(".btn-disassociate-file");
  if (!disassociateButtons.length) return;

  disassociateButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const articleId = this.getAttribute("data-article-id");
      const fileId = this.getAttribute("data-file-id");
      disassociateFile(articleId, fileId, this);
    });
  });
});

function disassociateFile(articleId, fileId, button) {
  if (!confirm("Remover associação deste arquivo?")) return;

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
