// -------------------------------------------------------------
// file-association.js
// Abre modal “Associar Arquivo Existente” e envia requisição AJAX
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  const associateButtons = document.querySelectorAll(".associate-file-btn");
  if (!associateButtons.length) return;

  associateButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const fileId = this.getAttribute("data-file-id");
      const fileName = this.getAttribute("data-file-name");
      const articleId = document.getElementById("article-id").value;

      document.getElementById("association-file-id").value = fileId;
      document.getElementById("association-article-id").value = articleId;
      document.getElementById("association-file-name").textContent = fileName;

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
});
