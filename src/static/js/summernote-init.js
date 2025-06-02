// -------------------------------------------------------------
// summernote-init.js
// Inicializa o editor Summernote e trata upload de imagens
// -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  const editorElement = document.querySelector("#editor");
  if (!editorElement) return;

  $("#editor").summernote({
    height: 300,
    lang: "pt-BR",
    dialogsInBody: true,
    disableDragAndDrop: true,
    callbacks: {
      onImageUpload: function (files) {
        for (let i = 0; i < files.length; i++) {
          uploadSummernoteImage(files[i]);
        }
      }
    }
  });
});

function uploadSummernoteImage(file) {
  const data = new FormData();
  data.append("file", file);

  const articleId = document.getElementById("article-id")?.value || "";
  fetch(`/articles/${articleId}/upload-image`, {
    method: "POST",
    body: data
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.url) {
        $("#editor").summernote("insertImage", data.url);
      } else {
        alert("Erro ao enviar imagem.");
      }
    })
    .catch(() => {
      alert("Erro ao enviar imagem.");
    });
}
