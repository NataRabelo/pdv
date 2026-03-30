const API_URL = "/api/produtos";

let produtosCache = [];
let categoriasCache = [];
let empresasCache = [];

document.addEventListener("DOMContentLoaded", async () => {
  bindEventosGlobais();
  bindFiltro();
  bindFormularioCadastro();
  bindFormularioEdicao();
  bindFormularioDelete();

  await carregarAuxiliares();
  await carregarProdutos();

  if (window.lucide) {
    lucide.createIcons();
  }
});

/* =========================
   MODAIS
========================= */
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  modal.classList.remove("hidden");
  modal.classList.add("flex");
  document.body.classList.add("overflow-hidden");

  if (window.lucide) {
    lucide.createIcons();
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  modal.classList.add("hidden");
  modal.classList.remove("flex");
  document.body.classList.remove("overflow-hidden");
}

/* =========================
   BINDERS
========================= */
function bindEventosGlobais() {
  document.addEventListener("click", function (e) {
    const editBtn = e.target.closest(".btn-editar-produto");
    if (editBtn) {
      abrirModalEdicao(editBtn.dataset.id);
      return;
    }

    const delBtn = e.target.closest(".btn-delete-produto");
    if (delBtn) {
      abrirModalDelete(delBtn.dataset.id);
      return;
    }

    const modal = e.target.closest("[id^='modal-']");
    if (modal && e.target === modal) {
      closeModal(modal.id);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;

    const modaisAbertos = document.querySelectorAll("[id^='modal-']:not(.hidden)");
    modaisAbertos.forEach((modal) => closeModal(modal.id));
  });
}

function bindFiltro() {
  const input = document.getElementById("filtro-produto");
  if (!input) return;

  input.addEventListener("input", function () {
    const termo = this.value.trim().toLowerCase();

    if (!termo) {
      renderTabela(produtosCache);
      return;
    }

    const filtrados = produtosCache.filter((p) =>
      [
        p.nome,
        p.codigo_barras,
        p.categoria_nome,
        p.empresa_nome,
        p.descricao
      ]
        .map((valor) => String(valor || "").toLowerCase())
        .join(" ")
        .includes(termo)
    );

    renderTabela(filtrados);
  });
}

function bindFormularioCadastro() {
  const formCadastro = document.getElementById("form-cadastrar-produto");
  if (!formCadastro) return;

  formCadastro.addEventListener("submit", async function (e) {
    e.preventDefault();

    const payload = getPayloadCadastro();

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || "Erro ao cadastrar produto.");
        return;
      }

      const novoProduto = data.data;
      produtosCache.unshift(novoProduto);

      removerLinhaVazia();

      const tbody = document.getElementById("produtos-body");
      if (tbody) {
        tbody.prepend(criarLinhaProduto(novoProduto));
      }

      this.reset();
      document.getElementById("ativo").checked = true;

      closeModal("modal-cadastrar-produto");

      if (window.lucide) {
        lucide.createIcons();
      }
    } catch (err) {
      console.error("Erro ao cadastrar produto:", err);
      alert("Erro ao cadastrar produto.");
    }
  });
}

function bindFormularioEdicao() {
  const formEdicao = document.getElementById("form-edicao-produto");
  if (!formEdicao) return;

  formEdicao.addEventListener("submit", async function (e) {
    e.preventDefault();

    const id = document.getElementById("edit-id")?.value;
    if (!id) {
      alert("Produto inválido para edição.");
      return;
    }

    const payload = getPayloadEdicao();

    try {
      const res = await fetch(`${API_URL}/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || "Erro ao atualizar produto.");
        return;
      }

      const produtoAtualizado = data.data;

      produtosCache = produtosCache.map((item) =>
        Number(item.id) === Number(id) ? produtoAtualizado : item
      );

      atualizarLinhaProduto(produtoAtualizado);
      closeModal("modal-edicao-produto");
    } catch (err) {
      console.error("Erro ao atualizar produto:", err);
      alert("Erro ao atualizar produto.");
    }
  });
}

function bindFormularioDelete() {
  const formDelete = document.getElementById("form-delete-produto");
  if (!formDelete) return;

  formDelete.addEventListener("submit", async function (e) {
    e.preventDefault();

    const id = document.getElementById("delete-id-produto")?.value;
    if (!id) {
      alert("Produto inválido para exclusão.");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/${id}`, {
        method: "DELETE"
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || "Erro ao deletar produto.");
        return;
      }

      produtosCache = produtosCache.filter(
        (item) => Number(item.id) !== Number(id)
      );

      removerLinhaProduto(id);
      closeModal("modal-deletar-produto");
    } catch (err) {
      console.error("Erro ao deletar produto:", err);
      alert("Erro ao deletar produto.");
    }
  });
}

/* =========================
   AUXILIARES
========================= */
async function carregarAuxiliares() {
  try {
    const res = await fetch(`${API_URL}/auxiliares`);
    const data = await res.json();

    if (!res.ok || !data.success) {
      console.error("Erro ao carregar auxiliares:", data.message);
      return;
    }

    categoriasCache = data.data?.categorias || [];
    empresasCache = data.data?.empresas || [];

    preencherSelect("categoria_id", categoriasCache);
    preencherSelect("edit-categoria_id", categoriasCache);

    preencherSelect("empresa_id", empresasCache);
    preencherSelect("edit-empresa_id", empresasCache);
  } catch (err) {
    console.error("Erro ao carregar auxiliares:", err);
  }
}

function preencherSelect(id, items) {
  const select = document.getElementById(id);
  if (!select) return;

  const valorAtual = select.value || "";
  const primeiraOption = `<option value="">Selecione</option>`;

  select.innerHTML =
    primeiraOption +
    items
      .map(
        (item) =>
          `<option value="${item.id}">${escapeHtml(
            item.nome_fantasia || item.nome || ""
          )}</option>`
      )
      .join("");

  if (valorAtual) {
    select.value = valorAtual;
  }
}

/* =========================
   LISTAR
========================= */
async function carregarProdutos() {
  try {
    const res = await fetch(API_URL);
    const data = await res.json();

    if (!res.ok || !data.success) {
      console.error("Erro ao listar produtos:", data.message);
      renderTabela([]);
      return;
    }

    produtosCache = Array.isArray(data.data) ? data.data : [];
    renderTabela(produtosCache);
  } catch (err) {
    console.error("Erro ao carregar produtos:", err);
    renderTabela([]);
  }
}

/* =========================
   RENDER
========================= */
function renderTabela(produtos) {
  const tbody = document.getElementById("produtos-body");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (!produtos.length) {
    tbody.innerHTML = `
      <tr id="linha-vazia">
        <td colspan="9" class="text-center text-slate-500 py-6">
          Nenhum produto cadastrado
        </td>
      </tr>
    `;
    return;
  }

  produtos.forEach((produto) => {
    tbody.appendChild(criarLinhaProduto(produto));
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

function criarLinhaProduto(produto) {
  const tr = document.createElement("tr");
  tr.setAttribute("data-id", produto.id);

  tr.innerHTML = `
    <td class="table-cell">
      <div class="font-semibold text-white">${escapeHtml(produto.nome)}</div>
      <div class="text-slate-400 text-xs">${escapeHtml(produto.descricao || "")}</div>
    </td>

    <td class="table-cell text-slate-300">${escapeHtml(produto.categoria_nome || "")}</td>
    <td class="table-cell text-slate-300">${escapeHtml(produto.empresa_nome || "")}</td>
    <td class="table-cell text-slate-300">${escapeHtml(produto.codigo_barras || "")}</td>
    <td class="table-cell text-slate-300">R$ ${formatMoney(produto.valor_compra)}</td>
    <td class="table-cell text-slate-300">R$ ${formatMoney(produto.valor_venda)}</td>
    <td class="table-cell text-slate-300">${formatNumber(produto.estoque_atual, 3)}</td>
    <td class="table-cell text-slate-300">${formatNumber(produto.estoque_minimo, 3)}</td>

    <td class="table-cell text-right">
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="btn-editar-produto p-2 text-sky-400 hover:text-sky-300 transition-all"
          data-id="${produto.id}"
          title="Editar"
        >
          <i data-lucide="square-pen" class="w-4 h-4"></i>
        </button>

        <button
          type="button"
          class="btn-delete-produto p-2 text-rose-400 hover:text-rose-300 transition-all"
          data-id="${produto.id}"
          title="Excluir"
        >
          <i data-lucide="trash-2" class="w-4 h-4"></i>
        </button>
      </div>
    </td>
  `;

  return tr;
}

function atualizarLinhaProduto(produto) {
  const tbody = document.getElementById("produtos-body");
  if (!tbody) return;

  const linhaExistente = tbody.querySelector(`tr[data-id="${produto.id}"]`);

  if (!linhaExistente) {
    removerLinhaVazia();
    tbody.prepend(criarLinhaProduto(produto));

    if (window.lucide) {
      lucide.createIcons();
    }
    return;
  }

  const novaLinha = criarLinhaProduto(produto);
  linhaExistente.replaceWith(novaLinha);

  if (window.lucide) {
    lucide.createIcons();
  }
}

function removerLinhaProduto(id) {
  const tbody = document.getElementById("produtos-body");
  if (!tbody) return;

  const linha = tbody.querySelector(`tr[data-id="${id}"]`);
  if (linha) {
    linha.remove();
  }

  if (!tbody.querySelector("tr[data-id]")) {
    tbody.innerHTML = `
      <tr id="linha-vazia">
        <td colspan="9" class="text-center text-slate-500 py-6">
          Nenhum produto cadastrado
        </td>
      </tr>
    `;
  }
}

function removerLinhaVazia() {
  const linhaVazia = document.getElementById("linha-vazia");
  if (linhaVazia) {
    linhaVazia.remove();
  }
}

/* =========================
   ABRIR MODAIS
========================= */
function abrirModalEdicao(id) {
  const produto = produtosCache.find((item) => Number(item.id) === Number(id));

  if (!produto) {
    alert("Produto não encontrado.");
    return;
  }

  document.getElementById("edit-id").value = produto.id || "";
  document.getElementById("edit-nome").value = produto.nome || "";
  document.getElementById("edit-descricao").value = produto.descricao || "";
  document.getElementById("edit-categoria_id").value = produto.categoria_id || "";
  document.getElementById("edit-empresa_id").value = produto.empresa_id || "";
  document.getElementById("edit-codigo_barras").value = produto.codigo_barras || "";
  document.getElementById("edit-possui_ncm").checked = !!produto.possui_ncm;
  document.getElementById("edit-ncm").value = produto.ncm || "";
  document.getElementById("edit-estoque_minimo").value = produto.estoque_minimo ?? 0;
  document.getElementById("edit-valor_compra").value = produto.valor_compra ?? 0;
  document.getElementById("edit-valor_venda").value = produto.valor_venda ?? 0;
  document.getElementById("edit-ativo").checked = produto.ativo !== false;

  openModal("modal-edicao-produto");
}

function abrirModalDelete(id) {
  document.getElementById("delete-id-produto").value = id;
  openModal("modal-deletar-produto");
}

/* =========================
   PAYLOADS
========================= */
function getPayloadCadastro() {
  return {
    nome: document.getElementById("nome")?.value.trim() || "",
    descricao: document.getElementById("descricao")?.value.trim() || "",
    categoria_id: normalizarValorSelect(document.getElementById("categoria_id")?.value),
    empresa_id: normalizarValorSelect(document.getElementById("empresa_id")?.value),
    codigo_barras: document.getElementById("codigo_barras")?.value.trim() || "",
    possui_ncm: !!document.getElementById("possui_ncm")?.checked,
    ncm: document.getElementById("ncm")?.value.trim() || "",
    estoque_minimo: document.getElementById("estoque_minimo")?.value || 0,
    valor_compra: document.getElementById("valor_compra")?.value || 0,
    valor_venda: document.getElementById("valor_venda")?.value || 0,
    ativo: !!document.getElementById("ativo")?.checked
  };
}

function getPayloadEdicao() {
  return {
    nome: document.getElementById("edit-nome")?.value.trim() || "",
    descricao: document.getElementById("edit-descricao")?.value.trim() || "",
    categoria_id: normalizarValorSelect(document.getElementById("edit-categoria_id")?.value),
    empresa_id: normalizarValorSelect(document.getElementById("edit-empresa_id")?.value),
    codigo_barras: document.getElementById("edit-codigo_barras")?.value.trim() || "",
    possui_ncm: !!document.getElementById("edit-possui_ncm")?.checked,
    ncm: document.getElementById("edit-ncm")?.value.trim() || "",
    estoque_minimo: document.getElementById("edit-estoque_minimo")?.value || 0,
    valor_compra: document.getElementById("edit-valor_compra")?.value || 0,
    valor_venda: document.getElementById("edit-valor_venda")?.value || 0,
    ativo: !!document.getElementById("edit-ativo")?.checked
  };
}

function normalizarValorSelect(value) {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  return value;
}

/* =========================
   HELPERS
========================= */
function formatMoney(value) {
  const number = Number(String(value ?? 0).replace(",", "."));
  return Number.isNaN(number) ? "0,00" : number.toFixed(2).replace(".", ",");
}

function formatNumber(value, decimals = 3) {
  const number = Number(String(value ?? 0).replace(",", "."));
  return Number.isNaN(number)
    ? Number(0).toFixed(decimals).replace(".", ",")
    : number.toFixed(decimals).replace(".", ",");
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}