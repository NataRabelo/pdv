window.produtoPage = null;

document.addEventListener("DOMContentLoaded", () => {
    window.produtoPage = new CrudPage({
        apiBaseUrl: "/api/produtos/",
        tableBodyId: "produto-table-body",
        formCreateId: "form-cadastro",
        formEditId: "form-edicao",
        formDeleteId: "form-delete",
        modalCreateId: "modal-cadastro",
        modalEditId: "modal-edicao",
        modalDeleteId: "modal-delete",
        searchInputId: "input-busca",
        fields: ["nome", "descricao", "categoria_nome", "empresa_nome", "codigo_barras"],

        messages: {
            loadError: "Erro ao carregar produtos.",
            createSuccess: "Produto cadastrado com sucesso.",
            createError: "Erro ao cadastrar produto.",
            updateSuccess: "Produto atualizado com sucesso.",
            updateError: "Erro ao atualizar produto.",
            deleteSuccess: "Produto excluído com sucesso.",
            deleteError: "Erro ao excluir produto."
        },

        mapItemToEditForm: (item) => ({
            nome: item.nome || "",
            descricao: item.descricao || "",
            categoria_id: item.categoria_id || "",
            empresa_id: item.empresa_id || "",
            codigo_barras: item.codigo_barras || "",
            possui_ncm: !!item.possui_ncm,
            ncm: item.ncm || "",
            estoque_minimo: normalizeDecimalForInput(item.estoque_minimo, 3),
            valor_compra: normalizeDecimalForInput(item.valor_compra, 2),
            valor_venda: normalizeDecimalForInput(item.valor_venda, 2),
            ativo: !!item.ativo
        }),

        renderRow: (item) => {
            const categoria = item.categoria_nome || "Sem categoria";
            const empresa = item.empresa_nome || "-";
            const codigoBarras = item.codigo_barras || "-";
            const estoqueAtual = formatNumber(item.estoque_atual, 3);
            const valorCompra = formatCurrency(item.valor_compra);
            const valorVenda = formatCurrency(item.valor_venda);
            const ativoBadge = item.ativo
                ? `<span class="inline-flex items-center rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-[11px] font-medium text-emerald-400">Ativo</span>`
                : `<span class="inline-flex items-center rounded-full bg-slate-700/40 border border-slate-700 px-2.5 py-1 text-[11px] font-medium text-slate-400">Inativo</span>`;

            return `
                <tr class="hover:bg-slate-800/40 transition">
                    <td class="px-5 py-4 align-middle">
                        <div class="flex items-start gap-3">
                            <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                                <i data-lucide="package" class="w-4 h-4"></i>
                            </div>
                            <div>
                                <p class="font-semibold text-white">${escapeHtml(item.nome || "-")}</p>
                                <p class="text-sm text-slate-400">${escapeHtml(item.descricao || "Sem descrição cadastrada.")}</p>
                                <div class="mt-2">${ativoBadge}</div>
                            </div>
                        </div>
                    </td>

                    <td class="px-5 py-4 align-middle text-slate-300">
                        ${escapeHtml(categoria)}
                    </td>

                    <td class="px-5 py-4 align-middle text-slate-300">
                        ${escapeHtml(empresa)}
                    </td>

                    <td class="px-5 py-4 align-middle text-slate-300">
                        ${escapeHtml(codigoBarras)}
                    </td>

                    <td class="px-5 py-4 align-middle text-right text-slate-300 font-medium">
                        ${estoqueAtual}
                    </td>

                    <td class="px-5 py-4 align-middle text-right text-slate-300 font-medium">
                        ${valorCompra}
                    </td>

                    <td class="px-5 py-4 align-middle text-right text-white font-semibold">
                        ${valorVenda}
                    </td>

                    <td class="px-5 py-4 align-middle">
                        <div class="flex items-center justify-center gap-2">
                            <button
                                type="button"
                                onclick="produtoPage.openEditModal(${item.id})"
                                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300 hover:bg-amber-400/20 transition"
                                title="Editar produto"
                            >
                                <i data-lucide="square-pen" class="w-4 h-4"></i>
                            </button>

                            <button
                                type="button"
                                onclick="produtoPage.openDeleteModal(${item.id})"
                                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition"
                                title="Excluir produto"
                            >
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }
    });

    enhanceProdutoPage(window.produtoPage);
    window.produtoPage.init();

    if (window.lucide) {
        lucide.createIcons();
    }
});

function enhanceProdutoPage(page) {
    page.auxiliares = {
        categorias: [],
        empresas: []
    };

    const originalInit = page.init.bind(page);
    page.init = async function () {
        this.bindCreateForm();
        this.bindEditForm();
        this.bindDeleteForm();
        this.bindSearch();
        this.bindModalClose();
        this.bindNcmToggle();
        await this.loadAuxiliares();
        await this.load();
    };

    page.loadAuxiliares = async function () {
        try {
            const result = await this.request(`${this.config.apiBaseUrl}auxiliares`, {
                method: "GET",
                headers: this.getHeaders(false)
            });

            this.auxiliares = result.data || { categorias: [], empresas: [] };
            this.populateAuxiliares();
        } catch (error) {
            this.showMessage(error.message || "Erro ao carregar dados auxiliares.", "error");
        }
    };

    page.populateAuxiliares = function () {
        populateSelect("cadastro-categoria_id", this.auxiliares.categorias, true);
        populateSelect("edicao-categoria_id", this.auxiliares.categorias, true);
        populateSelect("cadastro-empresa_id", this.auxiliares.empresas, false);
        populateSelect("edicao-empresa_id", this.auxiliares.empresas, false);
    };

    page.bindNcmToggle = function () {
        setupNcmToggle("cadastro-possui_ncm", "cadastro-ncm");
        setupNcmToggle("edicao-possui_ncm", "edicao-ncm");
    };

    const originalOpenCreateModal = page.openCreateModal.bind(page);
    page.openCreateModal = function () {
        originalOpenCreateModal();
        this.populateAuxiliares();

        const ativo = document.getElementById("cadastro-ativo");
        const possuiNcm = document.getElementById("cadastro-possui_ncm");
        const ncm = document.getElementById("cadastro-ncm");

        if (ativo) ativo.checked = true;
        if (possuiNcm) possuiNcm.checked = false;
        if (ncm) {
            ncm.value = "";
            ncm.disabled = true;
        }
    };

    const originalFillForm = page.fillForm.bind(page);
    page.fillForm = function (formId, data) {
        const form = document.getElementById(formId);
        if (!form) return;

        Object.keys(data).forEach((key) => {
            const field = form.querySelector(`[name="${key}"]`);
            if (!field) return;

            if (field.type === "checkbox") {
                field.checked = !!data[key];
            } else {
                field.value = data[key] ?? "";
            }
        });

        const possuiNcmField = form.querySelector(`[name="possui_ncm"]`);
        const ncmField = form.querySelector(`[name="ncm"]`);

        if (possuiNcmField && ncmField) {
            ncmField.disabled = !possuiNcmField.checked;
            if (!possuiNcmField.checked) {
                ncmField.value = "";
            }
        }

        if (window.lucide) {
            lucide.createIcons();
        }
    };

    const originalClearForm = page.clearForm.bind(page);
    page.clearForm = function (formId) {
        originalClearForm(formId);

        const form = document.getElementById(formId);
        if (!form) return;

        form.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
            checkbox.checked = false;
        });

        const ativo = form.querySelector('[name="ativo"]');
        if (ativo) ativo.checked = true;

        const ncm = form.querySelector('[name="ncm"]');
        if (ncm) {
            ncm.value = "";
            ncm.disabled = true;
        }

        const estoqueMinimo = form.querySelector('[name="estoque_minimo"]');
        const valorCompra = form.querySelector('[name="valor_compra"]');
        const valorVenda = form.querySelector('[name="valor_venda"]');

        if (estoqueMinimo) estoqueMinimo.value = "0";
        if (valorCompra) valorCompra.value = "0";
        if (valorVenda) valorVenda.value = "0";
    };
}

function populateSelect(selectId, items, allowEmptyOption) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const currentValue = select.value;

    select.innerHTML = "";

    if (allowEmptyOption) {
        select.innerHTML += `<option value="">Sem categoria</option>`;
    } else {
        select.innerHTML += `<option value="">Selecione</option>`;
    }

    (items || []).forEach((item) => {
        select.innerHTML += `<option value="${item.id}">${escapeHtml(item.nome)}</option>`;
    });

    if (currentValue) {
        select.value = currentValue;
    }
}

function setupNcmToggle(checkboxId, inputId) {
    const checkbox = document.getElementById(checkboxId);
    const input = document.getElementById(inputId);

    if (!checkbox || !input) return;

    const applyState = () => {
        input.disabled = !checkbox.checked;
        if (!checkbox.checked) {
            input.value = "";
        }
    };

    checkbox.addEventListener("change", applyState);
    applyState();
}

function normalizeDecimalForInput(value, decimals = 2) {
    if (value === null || value === undefined || value === "") {
        return "0";
    }

    const parsed = Number(String(value).replace(",", "."));
    if (Number.isNaN(parsed)) {
        return "0";
    }

    return parsed.toFixed(decimals);
}

function formatCurrency(value) {
    const parsed = Number(String(value ?? 0).replace(",", "."));
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function formatNumber(value, decimals = 3) {
    const parsed = Number(String(value ?? 0).replace(",", "."));
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}