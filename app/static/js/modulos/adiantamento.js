window.adiantamentoPage = {
    auxiliares: {
        empresas: [],
        funcionarios: [],
        formas_pagamento: [],
        produtos: []
    },
    registros: [],
    resumo: null,
    empresaId: "",
    funcionarioId: "",
    competencia: ""
};

document.addEventListener("DOMContentLoaded", async () => {
    adiantamentoPage.competencia = getCurrentMonthValue();

    bindAdiantamentoModalClose();
    bindAdiantamentoFilters();
    bindAdiantamentoForm();
    bindAdiantamentoHelpers();
    bindAdiantamentoMasks();

    await carregarAdiantamentoAuxiliares();

    if (adiantamentoPage.auxiliares.empresas.length === 1) {
        adiantamentoPage.empresaId = String(adiantamentoPage.auxiliares.empresas[0].id);
    }

    popularEmpresasAdiantamento();
    popularFormasAdiantamento();
    popularFuncionariosAdiantamento();
    popularProdutosAdiantamento();
    resetAdiantamentoForm();
    await carregarAdiantamentoTudo();

    if (window.lucide) {
        lucide.createIcons();
    }
});

async function carregarAdiantamentoAuxiliares() {
    const result = await requestAdiantamentoJson("/api/adiantamentos/auxiliares", { method: "GET" });
    adiantamentoPage.auxiliares = result.data || adiantamentoPage.auxiliares;
}

async function carregarAdiantamentoTudo() {
    await Promise.all([
        carregarResumoAdiantamento(),
        carregarListaAdiantamento()
    ]);
}

async function carregarResumoAdiantamento() {
    const url = new URL("/api/adiantamentos/resumo", window.location.origin);
    if (adiantamentoPage.empresaId) {
        url.searchParams.set("empresa_id", adiantamentoPage.empresaId);
    }
    if (adiantamentoPage.competencia) {
        url.searchParams.set("competencia", adiantamentoPage.competencia);
    }

    const result = await requestAdiantamentoJson(url.toString(), { method: "GET" });
    adiantamentoPage.resumo = result.data || null;
    renderResumoAdiantamento();
    atualizarKpisAdiantamento();
}

async function carregarListaAdiantamento() {
    const url = new URL("/api/adiantamentos/", window.location.origin);
    url.searchParams.set("limite", "120");
    if (adiantamentoPage.empresaId) {
        url.searchParams.set("empresa_id", adiantamentoPage.empresaId);
    }
    if (adiantamentoPage.funcionarioId) {
        url.searchParams.set("funcionario_id", adiantamentoPage.funcionarioId);
    }
    if (adiantamentoPage.competencia) {
        url.searchParams.set("competencia", adiantamentoPage.competencia);
    }

    const result = await requestAdiantamentoJson(url.toString(), { method: "GET" });
    adiantamentoPage.registros = Array.isArray(result.data) ? result.data : [];
    renderListaAdiantamento();
    atualizarKpisAdiantamento();
}

function bindAdiantamentoFilters() {
    const empresaSelect = document.getElementById("adiantamento-empresa");
    const funcionarioSelect = document.getElementById("adiantamento-funcionario");
    const competenciaInput = document.getElementById("adiantamento-competencia");
    const openButton = document.getElementById("adiantamento-open-create");
    const printButton = document.getElementById("adiantamento-print-report");

    if (empresaSelect) {
        empresaSelect.addEventListener("change", async () => {
            adiantamentoPage.empresaId = empresaSelect.value || "";
            adiantamentoPage.funcionarioId = "";
            popularEmpresasAdiantamento();
            popularFuncionariosAdiantamento();
            resetAdiantamentoForm();
            await carregarAdiantamentoTudo();
        });
    }

    if (funcionarioSelect) {
        funcionarioSelect.addEventListener("change", async () => {
            adiantamentoPage.funcionarioId = funcionarioSelect.value || "";
            await carregarListaAdiantamento();
        });
    }

    if (competenciaInput) {
        competenciaInput.value = adiantamentoPage.competencia;
        competenciaInput.addEventListener("change", async () => {
            adiantamentoPage.competencia = competenciaInput.value || getCurrentMonthValue();
            resetAdiantamentoForm();
            await carregarAdiantamentoTudo();
        });
    }

    if (openButton) {
        openButton.addEventListener("click", () => {
            resetAdiantamentoForm();
            abrirAdiantamentoModal("adiantamento-create-modal");
        });
    }

    if (printButton) {
        printButton.addEventListener("click", () => {
            const url = new URL("/api/financeiro/relatorios/adiantamentos/impressao", window.location.origin);
            if (adiantamentoPage.empresaId) {
                url.searchParams.set("empresa_id", adiantamentoPage.empresaId);
            }
            if (adiantamentoPage.competencia) {
                url.searchParams.set("competencia", adiantamentoPage.competencia);
            }
            window.open(url.toString(), "_blank", "noopener");
        });
    }
}

function bindAdiantamentoForm() {
    const form = document.getElementById("adiantamento-create-form");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            const payload = montarPayloadAdiantamento();
            const result = await requestAdiantamentoJson("/api/adiantamentos/", {
                method: "POST",
                headers: getAdiantamentoHeaders(true),
                body: JSON.stringify(payload)
            });

            showAdiantamentoMessage(result.message || "Adiantamento registrado com sucesso.", "success");
            fecharAdiantamentoModal("adiantamento-create-modal");
            resetAdiantamentoForm();
            await carregarAdiantamentoTudo();
        } catch (error) {
            showAdiantamentoMessage(error.message || "Erro ao registrar o vale.", "error");
        }
    });
}

function bindAdiantamentoHelpers() {
    const tipoSelect = document.getElementById("adiantamento-tipo");
    const empresaSelect = document.getElementById("adiantamento-empresa-form");
    const produtoSelect = document.getElementById("adiantamento-produto");
    const quantidadeInput = document.getElementById("adiantamento-quantidade");

    if (tipoSelect) {
        tipoSelect.addEventListener("change", () => {
            atualizarTipoAdiantamentoForm();
        });
    }

    if (empresaSelect) {
        empresaSelect.addEventListener("change", () => {
            popularFuncionariosAdiantamento();
            popularProdutosAdiantamento();
            atualizarPreviewProdutoAdiantamento();
        });
    }

    if (produtoSelect) {
        produtoSelect.addEventListener("change", () => {
            atualizarPreviewProdutoAdiantamento();
        });
    }

    if (quantidadeInput) {
        quantidadeInput.addEventListener("input", () => {
            atualizarPreviewProdutoAdiantamento();
        });
    }
}

function bindAdiantamentoMasks() {
    bindAdiantamentoMoneyMask("adiantamento-valor");
    bindAdiantamentoIntegerMask("adiantamento-quantidade");
}

function popularEmpresasAdiantamento() {
    const selects = [
        { element: document.getElementById("adiantamento-empresa"), allowAll: true },
        { element: document.getElementById("adiantamento-empresa-form"), allowAll: false }
    ];

    selects.forEach(({ element, allowAll }) => {
        if (!element) return;
        const valorAtual = element.value;
        element.innerHTML = allowAll ? `<option value="">Todas as empresas</option>` : `<option value="">Selecione</option>`;

        adiantamentoPage.auxiliares.empresas.forEach((empresa) => {
            const option = document.createElement("option");
            option.value = empresa.id;
            option.textContent = empresa.nome;
            if (String(empresa.id) === String(valorAtual || adiantamentoPage.empresaId || "")) {
                option.selected = true;
            }
            element.appendChild(option);
        });
    });
}

function popularFuncionariosAdiantamento() {
    const empresaFiltroPagina = adiantamentoPage.empresaId || "";
    const empresaFiltroFormulario = document.getElementById("adiantamento-empresa-form")?.value || adiantamentoPage.empresaId || "";
    const funcionariosPagina = filtrarFuncionariosAdiantamentoPorEmpresa(empresaFiltroPagina);
    const funcionariosFormulario = filtrarFuncionariosAdiantamentoPorEmpresa(empresaFiltroFormulario);

    const filterSelect = document.getElementById("adiantamento-funcionario");
    const formSelect = document.getElementById("adiantamento-funcionario-form");

    if (filterSelect) {
        filterSelect.innerHTML = `<option value="">Todos os funcionarios</option>`;
        funcionariosPagina.forEach((item) => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = item.nome;
            option.selected = String(item.id) === String(adiantamentoPage.funcionarioId || "");
            filterSelect.appendChild(option);
        });
    }

    if (formSelect) {
        const valorAtual = formSelect.value;
        formSelect.innerHTML = `<option value="">Selecione</option>`;
        funcionariosFormulario.forEach((item) => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = `${item.nome} - salario ${formatAdiantamentoCurrency(item.salario)}`;
            option.selected = String(item.id) === String(valorAtual || "");
            formSelect.appendChild(option);
        });
    }
}

function filtrarFuncionariosAdiantamentoPorEmpresa(empresaId) {
    return (adiantamentoPage.auxiliares.funcionarios || []).filter((item) => {
        if (!empresaId) return true;
        return Array.isArray(item.empresa_ids) && item.empresa_ids.some((id) => String(id) === String(empresaId));
    });
}

function popularFormasAdiantamento() {
    const select = document.getElementById("adiantamento-forma");
    if (!select) return;

    select.innerHTML = "";
    adiantamentoPage.auxiliares.formas_pagamento.forEach((item) => {
        const option = document.createElement("option");
        option.value = item.id;
        option.textContent = item.nome;
        select.appendChild(option);
    });

    const formaPadrao = adiantamentoPage.auxiliares.formas_pagamento.find((item) => item.nome === "Vale em folha");
    if (formaPadrao) {
        select.value = formaPadrao.id;
    }
}

function popularProdutosAdiantamento() {
    const empresaId = document.getElementById("adiantamento-empresa-form")?.value || "";
    const select = document.getElementById("adiantamento-produto");
    if (!select) return;

    const valorAtual = select.value;
    select.innerHTML = `<option value="">Selecione</option>`;

    (adiantamentoPage.auxiliares.produtos || [])
        .filter((item) => !empresaId || String(item.empresa_id) === String(empresaId))
        .forEach((item) => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = `${item.nome} - saldo ${formatAdiantamentoInteger(item.estoque_atual)}`;
            option.selected = String(item.id) === String(valorAtual || "");
            select.appendChild(option);
        });
}

function atualizarTipoAdiantamentoForm() {
    const tipo = document.getElementById("adiantamento-tipo")?.value || "DINHEIRO";
    const dinheiroGroup = document.getElementById("adiantamento-dinheiro-group");
    const produtoGroup = document.getElementById("adiantamento-produto-group");
    const quantidadeGroup = document.getElementById("adiantamento-quantidade-group");
    const previewBox = document.getElementById("adiantamento-preview-box");

    const isProduto = tipo === "PRODUTO";

    dinheiroGroup?.classList.toggle("hidden", isProduto);
    produtoGroup?.classList.toggle("hidden", !isProduto);
    quantidadeGroup?.classList.toggle("hidden", !isProduto);
    previewBox?.classList.toggle("hidden", !isProduto);

    atualizarPreviewProdutoAdiantamento();
}

function atualizarPreviewProdutoAdiantamento() {
    const produtoId = document.getElementById("adiantamento-produto")?.value || "";
    const quantidade = parseAdiantamentoInteger(document.getElementById("adiantamento-quantidade")?.value || "0");
    const produto = (adiantamentoPage.auxiliares.produtos || []).find((item) => String(item.id) === String(produtoId));

    const unitElement = document.getElementById("adiantamento-preview-unit");
    const totalElement = document.getElementById("adiantamento-preview-total");

    const unitario = parseAdiantamentoMoney(produto?.valor_venda || 0);
    const total = unitario * Math.max(quantidade, 0);

    if (unitElement) unitElement.textContent = formatAdiantamentoCurrency(unitario);
    if (totalElement) totalElement.textContent = formatAdiantamentoCurrency(total);
}

function renderResumoAdiantamento() {
    const container = document.getElementById("adiantamento-resumo-list");
    if (!container) return;

    const resumo = adiantamentoPage.resumo;
    if (!resumo || !Array.isArray(resumo.funcionarios) || !resumo.funcionarios.length) {
        container.innerHTML = `<p class="text-slate-400">Nenhum funcionario encontrado para a competencia selecionada.</p>`;
        return;
    }

    container.innerHTML = resumo.funcionarios.map((item) => `
        <article class="adiantamento-summary-card">
            <div class="flex items-start justify-between gap-4">
                <div>
                    <p class="font-semibold text-white">${escapeAdiantamentoHtml(item.funcionario_nome || "-")}</p>
                    <p class="text-sm text-slate-400">${escapeAdiantamentoHtml(item.empresa_nomes || "-")}</p>
                </div>
                <span class="text-xs uppercase tracking-[0.14em] text-slate-500">${formatAdiantamentoCompetencia(item.competencia)}</span>
            </div>
            <div class="adiantamento-summary-grid">
                <div>
                    <span class="adiantamento-summary-label">Salario</span>
                    <strong class="adiantamento-summary-value">${formatAdiantamentoCurrency(item.salario_base)}</strong>
                </div>
                <div>
                    <span class="adiantamento-summary-label">Total adiantado</span>
                    <strong class="adiantamento-summary-value">${formatAdiantamentoCurrency(item.total_adiantado)}</strong>
                </div>
                <div>
                    <span class="adiantamento-summary-label">Dinheiro</span>
                    <strong class="adiantamento-summary-value">${formatAdiantamentoCurrency(item.adiantamento_dinheiro)}</strong>
                </div>
                <div>
                    <span class="adiantamento-summary-label">Produtos</span>
                    <strong class="adiantamento-summary-value">${formatAdiantamentoCurrency(item.adiantamento_produto)}</strong>
                </div>
                <div>
                    <span class="adiantamento-summary-label">Saldo previsto</span>
                    <strong class="adiantamento-summary-value">${formatAdiantamentoCurrency(item.saldo_a_pagar)}</strong>
                </div>
                <div>
                    <span class="adiantamento-summary-label">Registros</span>
                    <strong class="adiantamento-summary-value">${formatAdiantamentoInteger(item.quantidade_registros)}</strong>
                </div>
            </div>
        </article>
    `).join("");
}

function renderListaAdiantamento() {
    const body = document.getElementById("adiantamento-table-body");
    if (!body) return;

    if (!adiantamentoPage.registros.length) {
        body.innerHTML = `
            <tr>
                <td colspan="6" class="px-5 py-8 text-center text-slate-400">Nenhum vale encontrado para o filtro atual.</td>
            </tr>
        `;
        return;
    }

    body.innerHTML = adiantamentoPage.registros.map((item) => {
        const badge = item.tipo_adiantamento === "PRODUTO"
            ? `<span class="adiantamento-badge adiantamento-badge-product">Produto</span>`
            : `<span class="adiantamento-badge adiantamento-badge-money">Dinheiro</span>`;

        const detalhe = item.tipo_adiantamento === "PRODUTO" && item.produto_nome
            ? `${escapeAdiantamentoHtml(item.produto_nome)} - ${formatAdiantamentoInteger(item.quantidade || 0)} un.`
            : escapeAdiantamentoHtml(item.descricao || "-");

        return `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="px-5 py-4 align-middle text-slate-300">${formatAdiantamentoDate(item.data_adiantamento)}</td>
                <td class="px-5 py-4 align-middle">
                    <p class="font-medium text-white">${escapeAdiantamentoHtml(item.funcionario_nome || "-")}</p>
                    <p class="text-xs text-slate-500">${escapeAdiantamentoHtml(item.empresa_nome || "-")}</p>
                </td>
                <td class="px-5 py-4 align-middle">${badge}</td>
                <td class="px-5 py-4 align-middle text-slate-300">
                    <p>${detalhe}</p>
                    <p class="text-xs text-slate-500 mt-1">${escapeAdiantamentoHtml(item.observacao || "")}</p>
                </td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeAdiantamentoHtml(item.forma_pagamento_nome || "-")}</td>
                <td class="px-5 py-4 align-middle text-right text-white font-semibold">${formatAdiantamentoCurrency(item.valor_total)}</td>
            </tr>
        `;
    }).join("");
}

function atualizarKpisAdiantamento() {
    const resumo = adiantamentoPage.resumo;
    const totais = resumo?.totais || {};
    setAdiantamentoText("adiantamento-kpi-funcionarios", String(totais.funcionarios || 0));
    setAdiantamentoText("adiantamento-kpi-total", formatAdiantamentoCurrency(totais.adiantado || 0));
    setAdiantamentoText("adiantamento-kpi-saldo", formatAdiantamentoCurrency(totais.saldo_a_pagar || 0));
    setAdiantamentoText("adiantamento-kpi-registros", String(adiantamentoPage.registros.length));
}

function resetAdiantamentoForm() {
    const empresaSelect = document.getElementById("adiantamento-empresa-form");
    const tipoSelect = document.getElementById("adiantamento-tipo");
    const valorInput = document.getElementById("adiantamento-valor");
    const quantidadeInput = document.getElementById("adiantamento-quantidade");
    const dataInput = document.getElementById("adiantamento-data");
    const competenciaInput = document.getElementById("adiantamento-competencia-form");
    const descricaoInput = document.getElementById("adiantamento-descricao");
    const observacaoInput = document.getElementById("adiantamento-observacao");

    if (empresaSelect) {
        empresaSelect.value = adiantamentoPage.empresaId || adiantamentoPage.auxiliares.empresas[0]?.id || "";
    }

    if (tipoSelect) tipoSelect.value = "DINHEIRO";
    if (valorInput) valorInput.value = "0,00";
    if (quantidadeInput) quantidadeInput.value = "1";
    if (dataInput) dataInput.value = new Date().toISOString().slice(0, 10);
    if (competenciaInput) competenciaInput.value = adiantamentoPage.competencia || getCurrentMonthValue();
    if (descricaoInput) descricaoInput.value = "";
    if (observacaoInput) observacaoInput.value = "";

    popularEmpresasAdiantamento();
    popularFuncionariosAdiantamento();
    popularProdutosAdiantamento();
    popularFormasAdiantamento();
    atualizarTipoAdiantamentoForm();
}

function montarPayloadAdiantamento() {
    const tipo = document.getElementById("adiantamento-tipo")?.value || "DINHEIRO";

    const payload = {
        tipo_adiantamento: tipo,
        forma_pagamento_id: document.getElementById("adiantamento-forma")?.value || "",
        empresa_id: document.getElementById("adiantamento-empresa-form")?.value || "",
        funcionario_id: document.getElementById("adiantamento-funcionario-form")?.value || "",
        data_adiantamento: document.getElementById("adiantamento-data")?.value || "",
        competencia: document.getElementById("adiantamento-competencia-form")?.value || "",
        descricao: (document.getElementById("adiantamento-descricao")?.value || "").trim(),
        observacao: (document.getElementById("adiantamento-observacao")?.value || "").trim()
    };

    if (tipo === "DINHEIRO") {
        payload.valor_total = normalizeAdiantamentoMoney(document.getElementById("adiantamento-valor")?.value || "0");
    } else {
        payload.produto_id = document.getElementById("adiantamento-produto")?.value || "";
        payload.quantidade = normalizeAdiantamentoInteger(document.getElementById("adiantamento-quantidade")?.value || "0");
    }

    return payload;
}

function requestAdiantamentoJson(url, options = {}) {
    return fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            ...getAdiantamentoHeaders(false),
            ...(options.headers || {})
        }
    }).then(async (response) => {
        let result;
        try {
            result = await response.json();
        } catch {
            result = { success: false, message: "Resposta invalida do servidor." };
        }

        if (!response.ok || result.success === false) {
            throw new Error(result.message || "Erro na requisicao.");
        }

        return result;
    });
}

function getAdiantamentoHeaders(isJson = false) {
    const token = localStorage.getItem("token");
    const headers = {};

    if (isJson) {
        headers["Content-Type"] = "application/json";
    }

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    return headers;
}

function bindAdiantamentoModalClose() {
    document.addEventListener("click", (event) => {
        const closeTrigger = event.target.closest("[data-close-modal]");
        if (!closeTrigger) return;

        const modalId = closeTrigger.getAttribute("data-close-modal");
        if (modalId) {
            fecharAdiantamentoModal(modalId);
        }
    });

    window.addEventListener("click", (event) => {
        if (event.target.classList.contains("modal-overlay")) {
            event.target.classList.add("hidden");
        }
    });
}

function abrirAdiantamentoModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("hidden");
}

function fecharAdiantamentoModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("hidden");
}

function showAdiantamentoMessage(message, type = "success") {
    const old = document.getElementById("crud-message");
    if (old) old.remove();

    const div = document.createElement("div");
    div.id = "crud-message";
    div.className = `
        fixed top-4 right-4 z-[9999] px-4 py-3 rounded-xl shadow-lg text-sm font-medium
        ${type === "success" ? "bg-emerald-500 text-white" : "bg-red-500 text-white"}
    `;
    div.textContent = message;
    document.body.appendChild(div);

    setTimeout(() => div.remove(), 3000);
}

function bindAdiantamentoMoneyMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    window.DecimalInput?.bind(input, {
        decimals: 2,
        allowEmpty: false
    });
}

function bindAdiantamentoIntegerMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.maskBound === "true") return;

    input.dataset.maskBound = "true";
    input.addEventListener("input", () => {
        input.value = formatAdiantamentoInteger(parseAdiantamentoInteger(input.value));
    });
    input.addEventListener("blur", () => {
        input.value = String(parseAdiantamentoInteger(input.value) || 1);
    });
}

function normalizeAdiantamentoMoney(value) {
    return window.DecimalInput?.normalize(value, 2) ?? "0.00";
}

function normalizeAdiantamentoInteger(value) {
    return String(parseAdiantamentoInteger(value));
}

function parseAdiantamentoMoney(value) {
    return window.DecimalInput?.parse(value) ?? 0;
}

function parseAdiantamentoInteger(value) {
    const digits = String(value ?? "").replace(/\D/g, "");
    const parsed = Number.parseInt(digits, 10);
    return Number.isNaN(parsed) ? 0 : parsed;
}

function formatAdiantamentoCurrency(value) {
    const parsed = Number(String(value ?? 0).replace(",", "."));
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function formatAdiantamentoCurrencyInput(value) {
    return window.DecimalInput?.format(value, 2, {
        allowEmpty: false,
        useGrouping: true
    }) ?? "0,00";
}

function formatAdiantamentoInteger(value) {
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(parseAdiantamentoInteger(value));
}

function formatAdiantamentoDate(value) {
    if (!value) return "-";
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return "-";
    return new Intl.DateTimeFormat("pt-BR").format(date);
}

function formatAdiantamentoCompetencia(value) {
    if (!value) return "-";
    const [ano, mes] = String(value).split("-");
    if (!ano || !mes) return value;
    return `${mes}/${ano}`;
}

function setAdiantamentoText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function getCurrentMonthValue() {
    const hoje = new Date();
    const mes = String(hoje.getMonth() + 1).padStart(2, "0");
    return `${hoje.getFullYear()}-${mes}`;
}

function escapeAdiantamentoHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
