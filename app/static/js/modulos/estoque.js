window.estoquePage = {
    saldos: [],
    movimentos: [],
    auxiliares: {
        empresas: [],
        produtos: [],
        motivos: {
            ENTRADA: [],
            SAIDA: []
        }
    },
    notificacoes: {
        resumo: {
            estoque_baixo: 0,
            sem_estoque: 0,
            vencidos: 0,
            proximos_vencimento: 0
        },
        estoque_baixo: [],
        sem_estoque: [],
        vencidos: [],
        proximos_vencimento: []
    },
    filtroEmpresa: "",
    busca: "",
    paginacao: {
        saldos: { paginaAtual: 1, porPagina: 8 },
        movimentos: { paginaAtual: 1, porPagina: 8 }
    }
};

document.addEventListener("DOMContentLoaded", async () => {
    bindModalClose();
    bindFilters();
    bindMovementForm();
    bindMovementHelpers();
    bindIntegerMask("movimento-quantidade");
    bindDecimalMask("movimento-valor_unitario", 2);

    await carregarTudo();

    const novaMovimentacaoBtn = document.getElementById("btn-nova-movimentacao");
    if (novaMovimentacaoBtn) {
        novaMovimentacaoBtn.addEventListener("click", abrirModalMovimentacao);
    }

    if (window.lucide) {
        lucide.createIcons();
    }
});

async function carregarTudo() {
    await Promise.all([
        carregarAuxiliares(),
        carregarSaldos(),
        carregarMovimentos(),
        carregarNotificacoes()
    ]);
}

async function carregarAuxiliares() {
    const result = await requestJson("/api/estoque/auxiliares", {
        method: "GET"
    });

    estoquePage.auxiliares = result.data || estoquePage.auxiliares;
    popularFiltroEmpresas();
    popularEmpresasModal();
    atualizarMotivos();
    atualizarProdutosModal();
}

async function carregarSaldos() {
    const url = new URL("/api/estoque/", window.location.origin);
    if (estoquePage.filtroEmpresa) {
        url.searchParams.set("empresa_id", estoquePage.filtroEmpresa);
    }

    const result = await requestJson(url.toString(), { method: "GET" });
    estoquePage.saldos = Array.isArray(result.data) ? result.data : [];
    renderTabelaEstoque();
    atualizarKpis();
}

async function carregarMovimentos() {
    const url = new URL("/api/estoque/movimentos", window.location.origin);
    url.searchParams.set("limite", "50");

    if (estoquePage.filtroEmpresa) {
        url.searchParams.set("empresa_id", estoquePage.filtroEmpresa);
    }

    const result = await requestJson(url.toString(), { method: "GET" });
    estoquePage.movimentos = Array.isArray(result.data) ? result.data : [];
    renderTabelaMovimentos();
}

async function carregarNotificacoes() {
    const url = new URL("/api/estoque/notificacoes", window.location.origin);
    url.searchParams.set("dias_vencimento", "30");

    if (estoquePage.filtroEmpresa) {
        url.searchParams.set("empresa_id", estoquePage.filtroEmpresa);
    }

    const result = await requestJson(url.toString(), { method: "GET" });
    estoquePage.notificacoes = result.data || estoquePage.notificacoes;
    renderNotificacoes();
    atualizarKpis();
}

function bindFilters() {
    const empresaFilter = document.getElementById("filtro-empresa");
    const buscaInput = document.getElementById("input-busca-estoque");

    if (empresaFilter) {
        empresaFilter.addEventListener("change", async () => {
            estoquePage.filtroEmpresa = empresaFilter.value || "";
            estoquePage.paginacao.saldos.paginaAtual = 1;
            estoquePage.paginacao.movimentos.paginaAtual = 1;
            await Promise.all([carregarSaldos(), carregarMovimentos(), carregarNotificacoes()]);
        });
    }

    if (buscaInput) {
        buscaInput.addEventListener("input", () => {
            estoquePage.busca = buscaInput.value || "";
            estoquePage.paginacao.saldos.paginaAtual = 1;
            renderTabelaEstoque();
        });
    }
}

function bindMovementForm() {
    const form = document.getElementById("form-movimentacao");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            const payload = normalizarPayloadMovimentacao();

            await requestJson("/api/estoque/movimentos/manual", {
                method: "POST",
                headers: getAuthHeaders(true),
                body: JSON.stringify(payload)
            });

            showMessage("Movimentação registrada com sucesso.", "success");
            fecharModal("modal-movimentacao");
            limparFormularioMovimentacao();
            await Promise.all([carregarSaldos(), carregarMovimentos(), carregarAuxiliares(), carregarNotificacoes()]);
        } catch (error) {
            showMessage(error.message || "Erro ao registrar movimentação.", "error");
        }
    });
}

function bindMovementHelpers() {
    const tipoSelect = document.getElementById("movimento-tipo_movimento");
    const empresaSelect = document.getElementById("movimento-empresa_id");
    const produtoSelect = document.getElementById("movimento-produto_empresa_id");

    if (tipoSelect) {
        tipoSelect.addEventListener("change", () => {
            atualizarMotivos();
        });
    }

    if (empresaSelect) {
        empresaSelect.addEventListener("change", () => {
            atualizarProdutosModal();
        });
    }

    if (produtoSelect) {
        produtoSelect.addEventListener("change", () => {
            atualizarHintProduto();
        });
    }
}

function popularFiltroEmpresas() {
    const select = document.getElementById("filtro-empresa");
    if (!select) return;

    const current = select.value;
    select.innerHTML = `<option value="">Todas as empresas</option>`;

    (estoquePage.auxiliares.empresas || []).forEach((empresa) => {
        const option = document.createElement("option");
        option.value = empresa.id;
        option.textContent = empresa.nome;
        if (String(empresa.id) === String(current || estoquePage.filtroEmpresa || "")) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function popularEmpresasModal() {
    const select = document.getElementById("movimento-empresa_id");
    if (!select) return;

    const current = select.value;
    select.innerHTML = `<option value="">Selecione</option>`;

    (estoquePage.auxiliares.empresas || []).forEach((empresa) => {
        const option = document.createElement("option");
        option.value = empresa.id;
        option.textContent = empresa.nome;
        if (String(empresa.id) === String(current || "")) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function atualizarMotivos() {
    const tipo = document.getElementById("movimento-tipo_movimento")?.value || "ENTRADA";
    const select = document.getElementById("movimento-motivo");
    if (!select) return;

    const motivos = estoquePage.auxiliares.motivos?.[tipo] || [];
    const current = select.value;
    select.innerHTML = "";

    motivos.forEach((motivo) => {
        const option = document.createElement("option");
        option.value = motivo;
        option.textContent = formatMotivo(motivo);
        if (motivo === current) {
            option.selected = true;
        }
        select.appendChild(option);
    });

    if (!select.value && motivos.length) {
        select.value = motivos[0];
    }
}

function atualizarProdutosModal() {
    const empresaId = document.getElementById("movimento-empresa_id")?.value || "";
    const select = document.getElementById("movimento-produto_empresa_id");
    if (!select) return;

    const produtos = (estoquePage.auxiliares.produtos || []).filter((item) => {
        if (!empresaId) return false;
        return String(item.empresa_id) === String(empresaId);
    });

    select.innerHTML = `<option value="">Selecione</option>`;

    produtos.forEach((produto) => {
        const option = document.createElement("option");
        option.value = produto.id;
        option.textContent = `${produto.nome} • saldo ${formatInteger(itemToInteger(produto.estoque_atual))}`;
        select.appendChild(option);
    });

    atualizarHintProduto();
}

function atualizarHintProduto() {
    const produtoEmpresaId = document.getElementById("movimento-produto_empresa_id")?.value || "";
    const hintProduto = document.getElementById("hint-produto");
    const hintEstoque = document.getElementById("hint-estoque");
    const hintMinimo = document.getElementById("hint-minimo");

    const item = (estoquePage.auxiliares.produtos || []).find((produto) => String(produto.id) === String(produtoEmpresaId));

    if (!item) {
        if (hintProduto) hintProduto.textContent = "Nenhum produto selecionado.";
        if (hintEstoque) hintEstoque.textContent = "0";
        if (hintMinimo) hintMinimo.textContent = "0";
        return;
    }

    if (hintProduto) {
        hintProduto.textContent = `${item.nome} • ${item.empresa_nome}`;
    }
    if (hintEstoque) {
        hintEstoque.textContent = formatInteger(item.estoque_atual);
    }
    if (hintMinimo) {
        hintMinimo.textContent = formatInteger(item.estoque_minimo);
    }
}

function atualizarKpis() {
    const totalProdutos = estoquePage.saldos.length;
    const abaixoMinimo = estoquePage.saldos.filter((item) => item.abaixo_minimo).length;
    const quantidadeTotal = estoquePage.saldos.reduce((sum, item) => sum + itemToInteger(item.estoque_atual), 0);
    const resumoNotificacoes = estoquePage.notificacoes?.resumo || {};

    setText("kpi-total-produtos", String(totalProdutos));
    setText("kpi-abaixo-minimo", String(abaixoMinimo));
    setText("kpi-quantidade-total", formatInteger(quantidadeTotal));
    setText("kpi-proximo-vencimento", String(resumoNotificacoes.proximos_vencimento || 0));
    setText("kpi-vencidos", String(resumoNotificacoes.vencidos || 0));
}

function renderTabelaEstoque() {
    const tableBody = document.getElementById("estoque-table-body");
    if (!tableBody) return;

    const termo = (estoquePage.busca || "").toLowerCase().trim();
    const items = estoquePage.saldos.filter((item) => {
        if (!termo) return true;

        return [
            item.nome,
            item.descricao,
            item.categoria_nome,
            item.empresa_nome,
            item.codigo_barras
        ].some((value) => String(value || "").toLowerCase().includes(termo));
    });

    const paginacao = estoquePage.paginacao.saldos;

    if (!items.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="px-5 py-8 text-center text-slate-400">
                    Nenhum produto encontrado para o filtro atual.
                </td>
            </tr>
        `;
        renderPagination("estoque-pagination", paginacao, items.length, () => renderTabelaEstoque());
        return;
    }

    const itensPagina = getPageItems(items, paginacao);

    tableBody.innerHTML = itensPagina.map((item) => {
        const statusBadge = item.abaixo_minimo
            ? `<span class="inline-flex items-center rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 text-[11px] font-medium text-amber-300">Baixo</span>`
            : `<span class="inline-flex items-center rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-[11px] font-medium text-emerald-300">Saudável</span>`;

        return `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="px-5 py-4 align-middle">
                    <div class="flex items-start gap-3">
                        <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                            <i data-lucide="boxes" class="w-4 h-4"></i>
                        </div>
                        <div>
                            <p class="font-semibold text-white">${escapeHtml(item.nome || "-")}</p>
                            <p class="text-sm text-slate-400">${escapeHtml(item.codigo_barras || "Sem código de barras")}</p>
                        </div>
                    </div>
                </td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeHtml(item.categoria_nome || "Sem categoria")}</td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeHtml(item.empresa_nome || "-")}</td>
                <td class="px-5 py-4 align-middle text-right text-white font-semibold">${formatInteger(item.estoque_atual)}</td>
                <td class="px-5 py-4 align-middle text-right text-slate-300">${formatInteger(item.estoque_minimo)}</td>
                <td class="px-5 py-4 align-middle text-slate-300">${formatValidadeEstoque(item.data_validade)}</td>
                <td class="px-5 py-4 align-middle text-right text-slate-300">${formatCurrency(item.valor_compra)}</td>
                <td class="px-5 py-4 align-middle text-right text-slate-300">${formatCurrency(item.valor_venda)}</td>
                <td class="px-5 py-4 align-middle text-center">${statusBadge}</td>
            </tr>
        `;
    }).join("");

    renderPagination("estoque-pagination", paginacao, items.length, () => renderTabelaEstoque());

    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderTabelaMovimentos() {
    const tableBody = document.getElementById("movimento-table-body");
    if (!tableBody) return;

    const paginacao = estoquePage.paginacao.movimentos;

    if (!estoquePage.movimentos.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="px-5 py-8 text-center text-slate-400">
                    Nenhuma movimentação encontrada.
                </td>
            </tr>
        `;
        renderPagination("movimento-pagination", paginacao, 0, () => renderTabelaMovimentos());
        return;
    }

    const itensPagina = getPageItems(estoquePage.movimentos, paginacao);

    tableBody.innerHTML = itensPagina.map((item) => {
        const tipoBadge = item.tipo_movimento === "ENTRADA"
            ? `<span class="inline-flex items-center rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-[11px] font-medium text-emerald-300">Entrada</span>`
            : `<span class="inline-flex items-center rounded-full bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 text-[11px] font-medium text-rose-300">Saída</span>`;

        const origemBadge = item.origem === "PDV"
            ? `<span class="inline-flex items-center rounded-full bg-sky-500/10 border border-sky-500/20 px-2.5 py-1 text-[11px] font-medium text-sky-300">PDV</span>`
            : item.origem === "VALE"
                ? `<span class="inline-flex items-center rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 text-[11px] font-medium text-amber-300">Vale</span>`
                : `<span class="inline-flex items-center rounded-full bg-slate-700/40 border border-slate-700 px-2.5 py-1 text-[11px] font-medium text-slate-300">Manual</span>`;

        return `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="px-5 py-4 align-middle text-slate-300">${formatDate(item.data_movimento)}</td>
                <td class="px-5 py-4 align-middle">
                    <p class="font-medium text-white">${escapeHtml(item.produto_nome || "-")}</p>
                    <p class="text-xs text-slate-500">${escapeHtml(item.funcionario_nome || "Sem responsável")}</p>
                </td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeHtml(item.empresa_nome || "-")}</td>
                <td class="px-5 py-4 align-middle">${origemBadge}</td>
                <td class="px-5 py-4 align-middle">${tipoBadge}</td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeHtml(formatMotivo(item.motivo))}</td>
                <td class="px-5 py-4 align-middle text-right text-white font-semibold">${formatInteger(item.quantidade)}</td>
                <td class="px-5 py-4 align-middle text-right text-slate-300">${item.valor_total ? formatCurrency(item.valor_total) : "-"}</td>
            </tr>
        `;
    }).join("");

    renderPagination("movimento-pagination", paginacao, estoquePage.movimentos.length, () => renderTabelaMovimentos());
}

function abrirModalMovimentacao() {
    limparFormularioMovimentacao();
    popularEmpresasModal();

    const empresaSelect = document.getElementById("movimento-empresa_id");
    if (empresaSelect && estoquePage.filtroEmpresa) {
        empresaSelect.value = estoquePage.filtroEmpresa;
    }

    atualizarMotivos();
    atualizarProdutosModal();
    abrirModal("modal-movimentacao");
}

function renderNotificacoes() {
    const estoqueContainer = document.getElementById("estoque-alertas-lista");
    const validadeContainer = document.getElementById("estoque-validade-lista");
    const notificacoes = estoquePage.notificacoes || {};

    if (estoqueContainer) {
        const itens = [
            ...(notificacoes.sem_estoque || []).map((item) => ({
                ...item,
                tipo: "Sem estoque",
                classe: "text-rose-300"
            })),
            ...(notificacoes.estoque_baixo || []).map((item) => ({
                ...item,
                tipo: "Baixo estoque",
                classe: "text-amber-300"
            }))
        ].slice(0, 10);

        estoqueContainer.innerHTML = itens.length
            ? itens.map((item) => `
                <article class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                    <div class="flex items-start justify-between gap-4">
                        <div>
                            <p class="font-medium text-white">${escapeHtml(item.nome || "-")}</p>
                            <p class="text-sm text-slate-400">${escapeHtml(item.empresa_nome || "-")}</p>
                        </div>
                        <span class="text-xs font-semibold ${item.classe}">${item.tipo}</span>
                    </div>
                    <div class="mt-3 flex items-center justify-between gap-3 text-sm text-slate-300">
                        <span>Atual ${formatInteger(item.estoque_atual)}</span>
                        <span>Minimo ${formatInteger(item.estoque_minimo)}</span>
                    </div>
                </article>
            `).join("")
            : `<p class="text-slate-400">Nenhum alerta de estoque no momento.</p>`;
    }

    if (validadeContainer) {
        const itens = [
            ...(notificacoes.vencidos || []).map((item) => ({
                ...item,
                tipo: "Vencido",
                detalhe: `${Math.abs(Number(item.dias_para_vencimento || 0))} dia(s) atras`,
                classe: "text-rose-300"
            })),
            ...(notificacoes.proximos_vencimento || []).map((item) => ({
                ...item,
                tipo: "A vencer",
                detalhe: `${Number(item.dias_para_vencimento || 0)} dia(s)`,
                classe: "text-sky-300"
            }))
        ].slice(0, 10);

        validadeContainer.innerHTML = itens.length
            ? itens.map((item) => `
                <article class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                    <div class="flex items-start justify-between gap-4">
                        <div>
                            <p class="font-medium text-white">${escapeHtml(item.nome || "-")}</p>
                            <p class="text-sm text-slate-400">${escapeHtml(item.empresa_nome || "-")}</p>
                        </div>
                        <span class="text-xs font-semibold ${item.classe}">${item.tipo}</span>
                    </div>
                    <div class="mt-3 flex items-center justify-between gap-3 text-sm text-slate-300">
                        <span>${formatValidadeEstoque(item.data_validade)}</span>
                        <span>${item.detalhe}</span>
                    </div>
                </article>
            `).join("")
            : `<p class="text-slate-400">Nenhum alerta de validade no momento.</p>`;
    }
}

function limparFormularioMovimentacao() {
    const form = document.getElementById("form-movimentacao");
    if (form) form.reset();

    const tipo = document.getElementById("movimento-tipo_movimento");
    const quantidade = document.getElementById("movimento-quantidade");
    const valorUnitario = document.getElementById("movimento-valor_unitario");

    if (tipo) tipo.value = "ENTRADA";
    if (quantidade) quantidade.value = "0";
    if (valorUnitario) valorUnitario.value = "";

    atualizarMotivos();
    atualizarProdutosModal();
}

function normalizarPayloadMovimentacao() {
    return {
        tipo_movimento: document.getElementById("movimento-tipo_movimento")?.value || "",
        motivo: document.getElementById("movimento-motivo")?.value || "",
        empresa_id: document.getElementById("movimento-empresa_id")?.value || "",
        produto_empresa_id: document.getElementById("movimento-produto_empresa_id")?.value || "",
        quantidade: normalizeIntegerForApi(document.getElementById("movimento-quantidade")?.value || "0"),
        valor_unitario: normalizeOptionalDecimalForApi(document.getElementById("movimento-valor_unitario")?.value || "", 2),
        observacao: (document.getElementById("movimento-observacao")?.value || "").trim()
    };
}

function bindDecimalMask(inputId, decimals) {
    const input = document.getElementById(inputId);
    if (!input) return;

    window.DecimalInput?.bind(input, {
        decimals,
        allowEmpty: true
    });
}

function bindIntegerMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input || input.dataset.maskBound === "true") return;

    input.dataset.maskBound = "true";
    input.addEventListener("input", () => {
        input.value = formatInteger(itemToInteger(input.value));
    });
    input.addEventListener("blur", () => {
        input.value = String(itemToInteger(input.value));
    });
}

function requestJson(url, options = {}) {
    return fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            ...getAuthHeaders(false),
            ...(options.headers || {})
        }
    }).then(async (response) => {
        let result;
        try {
            result = await response.json();
        } catch {
            result = { success: false, message: "Resposta inválida do servidor." };
        }

        if (!response.ok || result.success === false) {
            throw new Error(result.message || "Erro na requisição.");
        }

        return result;
    });
}

function getAuthHeaders(isJson = false) {
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

function bindModalClose() {
    document.addEventListener("click", (event) => {
        const closeTrigger = event.target.closest("[data-close-modal]");
        if (!closeTrigger) return;

        const modalId = closeTrigger.getAttribute("data-close-modal");
        if (modalId) {
            fecharModal(modalId);
        }
    });

    window.addEventListener("click", (event) => {
        if (event.target.classList.contains("modal-overlay")) {
            event.target.classList.add("hidden");
        }
    });
}

function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("hidden");
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("hidden");
}

function showMessage(message, type = "success") {
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

function normalizeDecimalForApi(value, decimals = 2) {
    return parseDecimal(value).toFixed(decimals);
}

function normalizeOptionalDecimalForApi(value, decimals = 2) {
    if (!String(value || "").trim()) {
        return "";
    }
    return normalizeDecimalForApi(value, decimals);
}

function normalizeIntegerForApi(value) {
    return String(itemToInteger(value));
}

function parseDecimal(value) {
    return window.DecimalInput?.parse(value) ?? 0;
}

function formatDecimalFromDigits(value, decimals = 2) {
    const digits = String(value ?? "").replace(/\D/g, "");

    if (!digits) {
        return decimals === 3 ? "0,000" : "";
    }

    const numericValue = Number(digits) / (10 ** decimals);
    return formatNumber(numericValue, decimals);
}

function formatNumber(value, decimals = 3) {
    const parsed = Number(String(value ?? 0).replace(",", "."));
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function formatInteger(value) {
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(itemToInteger(value));
}

function formatCurrency(value) {
    const parsed = Number(String(value ?? 0).replace(",", "."));
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";

    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short"
    }).format(date);
}

function formatValidadeEstoque(value) {
    if (!value) return "Sem validade";
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return "Sem validade";
    return new Intl.DateTimeFormat("pt-BR").format(date);
}

function formatMotivo(value) {
    const mapa = {
        COMPRA: "Compra",
        VENDA: "Venda",
        AJUSTE: "Ajuste",
        PERDA: "Perda",
        DEVOLUCAO: "Devolução",
        TRANSFERENCIA: "Transferência"
    };

    return mapa[value] || value || "-";
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function itemToInteger(value) {
    if (typeof value === "number" && Number.isInteger(value)) {
        return value;
    }

    const digits = String(value ?? "").replace(/\D/g, "");
    if (!digits) return 0;

    const parsed = Number.parseInt(digits, 10);
    return Number.isNaN(parsed) ? 0 : parsed;
}

function getPageItems(items, paginacao) {
    const totalPaginas = Math.max(Math.ceil(items.length / paginacao.porPagina), 1);
    if (paginacao.paginaAtual > totalPaginas) {
        paginacao.paginaAtual = totalPaginas;
    }

    const inicio = (paginacao.paginaAtual - 1) * paginacao.porPagina;
    return items.slice(inicio, inicio + paginacao.porPagina);
}

function renderPagination(containerId, paginacao, totalItens, onChange) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const totalPaginas = Math.max(Math.ceil(totalItens / paginacao.porPagina), 1);

    if (!totalItens || totalPaginas <= 1) {
        container.innerHTML = totalItens
            ? `<div class="pagination-summary px-5 py-4">Exibindo ${totalItens} registro(s).</div>`
            : "";
        return;
    }

    const inicio = ((paginacao.paginaAtual - 1) * paginacao.porPagina) + 1;
    const fim = Math.min(paginacao.paginaAtual * paginacao.porPagina, totalItens);
    const paginas = buildPageNumbers(paginacao.paginaAtual, totalPaginas);

    container.innerHTML = `
        <div class="pagination-shell">
            <div class="pagination-summary">Exibindo ${inicio}-${fim} de ${totalItens} registros</div>
            <div class="pagination-controls">
                <button type="button" class="pagination-btn" data-page="${paginacao.paginaAtual - 1}" ${paginacao.paginaAtual === 1 ? "disabled" : ""}>Anterior</button>
                ${paginas.map((pagina) => pagina === "..."
                    ? `<span class="pagination-ellipsis">...</span>`
                    : `<button type="button" class="pagination-btn ${pagina === paginacao.paginaAtual ? "pagination-btn-active" : ""}" data-page="${pagina}">${pagina}</button>`
                ).join("")}
                <button type="button" class="pagination-btn" data-page="${paginacao.paginaAtual + 1}" ${paginacao.paginaAtual === totalPaginas ? "disabled" : ""}>Próxima</button>
            </div>
        </div>
    `;

    container.querySelectorAll("[data-page]").forEach((button) => {
        button.addEventListener("click", () => {
            const pagina = Number(button.getAttribute("data-page"));
            if (!Number.isInteger(pagina)) return;
            paginacao.paginaAtual = Math.min(Math.max(pagina, 1), totalPaginas);
            onChange();
        });
    });
}

function buildPageNumbers(paginaAtual, totalPaginas) {
    if (totalPaginas <= 7) {
        return Array.from({ length: totalPaginas }, (_, index) => index + 1);
    }

    if (paginaAtual <= 4) {
        return [1, 2, 3, 4, 5, "...", totalPaginas];
    }

    if (paginaAtual >= totalPaginas - 3) {
        return [1, "...", totalPaginas - 4, totalPaginas - 3, totalPaginas - 2, totalPaginas - 1, totalPaginas];
    }

    return [1, "...", paginaAtual - 1, paginaAtual, paginaAtual + 1, "...", totalPaginas];
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
