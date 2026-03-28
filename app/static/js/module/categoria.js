lucide.createIcons();

function openModal(id) {
  const modal = document.getElementById(id);
  modal.style.display = "flex";
}

function closeModal(id) {
  const modal = document.getElementById(id);
  modal.style.display = "none";
}

function abrirModalEdicao(id, nome, descricao) {
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-nome').value = nome;
    document.getElementById('edit-descricao').value = descricao;

    // Define a action do form dinamicamente
    document.getElementById('form-edicao').action = `/editar-categoria/${id}`;

    openModal('modal-edicao');
}

// Fechar ao clicar fora do modal
window.onclick = function (event) {
  if (event.target.classList.contains("modal-overlay")) {
    event.target.style.display = "none";
  }
};
