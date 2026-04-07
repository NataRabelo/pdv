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
        paginationContainerId: "produto-pagination",
        pageSize: 10,
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
            estoque_minimo: formatIntegerForDisplay(item.estoque_minimo),
            valor_compra: formatDecimalForDisplay(item.valor_compra, 2),
            valor_venda: formatDecimalForDisplay(item.valor_venda, 2),
            ativo: !!item.ativo
        }),

        beforeSubmitCreate: (payload) => normalizeProdutoPayload(payload, false),
        beforeSubmitEdit: (payload) => normalizeProdutoPayload(payload, true),

        renderRow: (item) => {
            const categoria = item.categoria_nome || "Sem categoria";
            const empresa = item.empresa_nome || "-";
            const codigoBarras = item.codigo_barras || "-";
            const estoqueAtual = formatInteger(item.estoque_atual);
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
        this.bindMasks();
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

    page.bindMasks = function () {
        setupIntegerMask("cadastro-estoque_minimo");
        setupIntegerMask("edicao-estoque_minimo");
        setupDecimalMask("cadastro-valor_compra", 2);
        setupDecimalMask("edicao-valor_compra", 2);
        setupDecimalMask("cadastro-valor_venda", 2);
        setupDecimalMask("edicao-valor_venda", 2);
        setupDigitsMask("cadastro-codigo_barras", 50);
        setupDigitsMask("edicao-codigo_barras", 50);
        setupNcmMask("cadastro-ncm");
        setupNcmMask("edicao-ncm");
    };

    const originalOpenCreateModal = page.openCreateModal.bind(page);
    page.openCreateModal = async function () {
        await originalOpenCreateModal();
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

        applyIntegerDisplay("cadastro-estoque_minimo");
        applyDecimalDisplay("cadastro-valor_compra", 2);
        applyDecimalDisplay("cadastro-valor_venda", 2);
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
        if (valorCompra) valorCompra.value = "0,00";
        if (valorVenda) valorVenda.value = "0,00";
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

function normalizeProdutoPayload(payload, isEdit) {
    const data = { ...payload };

    data.nome = (data.nome || "").trim();
    data.descricao = (data.descricao || "").trim();
    data.categoria_id = data.categoria_id || "";
    data.empresa_id = data.empresa_id || "";
    data.codigo_barras = normalizeDigits(data.codigo_barras, 50);
    data.possui_ncm = getCheckboxValue(isEdit ? "edicao-possui_ncm" : "cadastro-possui_ncm");
    data.ncm = normalizeNcm(data.ncm);
    data.estoque_minimo = normalizeIntegerForApi(data.estoque_minimo);
    data.valor_compra = normalizeDecimalForApi(data.valor_compra, 2);
    data.valor_venda = normalizeDecimalForApi(data.valor_venda, 2);
    data.ativo = getCheckboxValue(isEdit ? "edicao-ativo" : "cadastro-ativo");

    if (!data.possui_ncm) {
        data.ncm = "";
    }

    return data;
}

function normalizeDecimalForApi(value, decimals = 2) {
    const normalized = parseDecimalInput(value);
    const fixed = normalized.toFixed(decimals);
    return decimals > 0 ? fixed : String(Math.trunc(normalized));
}

function formatDecimalForDisplay(value, decimals = 2) {
    if (value === null || value === undefined || value === "") {
        return formatNumber(0, decimals);
    }

    const parsed = Number(String(value).replace(",", "."));
    if (Number.isNaN(parsed)) {
        return formatNumber(0, decimals);
    }

    return formatNumber(parsed, decimals);
}

function formatIntegerForDisplay(value) {
    if (value === null || value === undefined || value === "") {
        return "0";
    }

    return formatInteger(value);
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

function formatInteger(value) {
    const parsed = Number.parseInt(String(value ?? 0).replace(/\D/g, ""), 10);
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function setupDecimalMask(inputId, decimals = 2) {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.maskBound === "true") return;

    input.dataset.maskBound = "true";
    input.setAttribute("inputmode", "decimal");

    const applyMask = () => {
        input.value = formatDecimalFromDigits(input.value, decimals);
    };

    input.addEventListener("input", applyMask);
    input.addEventListener("blur", applyMask);
    applyMask();
}

function setupIntegerMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.maskBound === "true") return;

    input.dataset.maskBound = "true";
    input.setAttribute("inputmode", "numeric");

    const applyMask = () => {
        input.value = formatIntegerInput(input.value);
    };

    input.addEventListener("input", applyMask);
    input.addEventListener("blur", applyMask);
    applyMask();
}

function setupDigitsMask(inputId, maxLength = 50) {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.maskBound === "true") return;

    input.dataset.maskBound = "true";
    input.setAttribute("inputmode", "numeric");

    input.addEventListener("input", () => {
        input.value = normalizeDigits(input.value, maxLength);
    });
}

function setupNcmMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.maskBound === "true") return;

    input.dataset.maskBound = "true";
    input.setAttribute("inputmode", "numeric");

    input.addEventListener("input", () => {
        input.value = formatNcm(input.value);
    });
}

function formatDecimalFromDigits(value, decimals = 2) {
    const digits = String(value ?? "").replace(/\D/g, "");

    if (!digits) {
        return formatNumber(0, decimals);
    }

    const numericValue = Number(digits) / (10 ** decimals);
    return formatNumber(numericValue, decimals);
}

function parseDecimalInput(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return 0;

    const normalized = raw
        .replace(/\./g, "")
        .replace(",", ".");

    const parsed = Number(normalized);
    return Number.isNaN(parsed) ? 0 : parsed;
}

function parseIntegerInput(value) {
    const digits = String(value ?? "").replace(/\D/g, "");
    if (!digits) return 0;

    const parsed = Number.parseInt(digits, 10);
    return Number.isNaN(parsed) ? 0 : parsed;
}

function normalizeDigits(value, maxLength = 50) {
    return String(value ?? "").replace(/\D/g, "").slice(0, maxLength);
}

function normalizeIntegerForApi(value) {
    return String(parseIntegerInput(value));
}

function formatNcm(value) {
    const digits = normalizeDigits(value, 8);

    if (digits.length <= 4) return digits;
    if (digits.length <= 6) return digits.replace(/^(\d{4})(\d+)/, "$1.$2");
    return digits.replace(/^(\d{4})(\d{2})(\d{0,2}).*/, "$1.$2.$3");
}

function normalizeNcm(value) {
    return normalizeDigits(value, 8);
}

function getCheckboxValue(inputId) {
    const input = document.getElementById(inputId);
    return !!input?.checked;
}

function applyDecimalDisplay(inputId, decimals = 2) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.value = formatDecimalForDisplay(input.value, decimals);
}

function applyIntegerDisplay(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.value = formatIntegerInput(input.value);
}

function formatIntegerInput(value) {
    return formatInteger(parseIntegerInput(value));
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
