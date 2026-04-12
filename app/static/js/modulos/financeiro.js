window.financeiroPage = {
    auxiliares: {
        empresas: [],
        formas_pagamento: [],
        categorias: { ENTRADA: [], SAIDA: [] }
    },
    dashboard: null,
    lancamentos: [],
    fechamentos: [],
    empresaId: "",
    periodoDias: "30",
    tipoLancamento: "",
    paginacao: {
        lancamentos: { paginaAtual: 1, porPagina: 10 },
        fechamentos: { paginaAtual: 1, porPagina: 10 }
    }
};

document.addEventListener("DOMContentLoaded", async () => {
    bindFinanceiroModalClose();
    bindFinanceiroFilters();
    bindFinanceiroActions();
    bindFinanceiroMasks();

    await carregarFinanceiroAuxiliares();

    if (financeiroPage.auxiliares.empresas.length === 1) {
        financeiroPage.empresaId = String(financeiroPage.auxiliares.empresas[0].id);
    }

    popularEmpresasFinanceiro();
    popularSelectsFinanceiro();
    await carregarFinanceiroTudo();

    if (window.lucide) {
        lucide.createIcons();
    }
});

function financeiroNeedsDashboard() {
    return Boolean(
        document.getElementById("financeiro-serie-list")
        || document.getElementById("financeiro-mensal-list")
        || document.getElementById("financeiro-kpi-saldo")
    );
}

function financeiroNeedsLancamentos() {
    return Boolean(document.getElementById("financeiro-lancamentos-body"));
}

function financeiroNeedsFechamentos() {
    return Boolean(document.getElementById("financeiro-fechamentos-body"));
}

async function carregarFinanceiroAuxiliares() {
    const result = await requestFinanceiroJson("/api/financeiro/auxiliares", { method: "GET" });
    financeiroPage.auxiliares = result.data || financeiroPage.auxiliares;
}

async function carregarFinanceiroTudo() {
    const tarefas = [];

    if (financeiroNeedsDashboard()) {
        tarefas.push(carregarDashboardFinanceiro());
    }
    if (financeiroNeedsLancamentos()) {
        tarefas.push(carregarLancamentosFinanceiro());
    }
    if (financeiroNeedsFechamentos()) {
        tarefas.push(carregarFechamentosFinanceiro());
    }

    await Promise.all(tarefas);
}

async function carregarDashboardFinanceiro() {
    const url = new URL("/api/financeiro/dashboard", window.location.origin);
    url.searchParams.set("periodo_dias", financeiroPage.periodoDias || "30");
    if (financeiroPage.empresaId) {
        url.searchParams.set("empresa_id", financeiroPage.empresaId);
    }

    const result = await requestFinanceiroJson(url.toString(), { method: "GET" });
    financeiroPage.dashboard = result.data || null;
    renderDashboardFinanceiro();
}

async function carregarLancamentosFinanceiro() {
    const url = new URL("/api/financeiro/lancamentos", window.location.origin);
    url.searchParams.set("limite", "500");
    if (financeiroPage.empresaId) {
        url.searchParams.set("empresa_id", financeiroPage.empresaId);
    }
    if (financeiroPage.tipoLancamento) {
        url.searchParams.set("tipo", financeiroPage.tipoLancamento);
    }

    const result = await requestFinanceiroJson(url.toString(), { method: "GET" });
    financeiroPage.lancamentos = Array.isArray(result.data) ? result.data : [];
    renderLancamentosFinanceiro();
}

async function carregarFechamentosFinanceiro() {
    const url = new URL("/api/financeiro/fechamentos", window.location.origin);
    url.searchParams.set("limite", "500");
    if (financeiroPage.empresaId) {
        url.searchParams.set("empresa_id", financeiroPage.empresaId);
    }

    const result = await requestFinanceiroJson(url.toString(), { method: "GET" });
    financeiroPage.fechamentos = Array.isArray(result.data) ? result.data : [];
    renderFechamentosFinanceiro();
}

function bindFinanceiroFilters() {
    const empresaSelect = document.getElementById("financeiro-empresa");
    const periodoSelect = document.getElementById("financeiro-periodo");
    const tipoSelect = document.getElementById("financeiro-tipo");
    const launchTipo = document.getElementById("financeiro-launch-tipo");

    if (empresaSelect) {
        empresaSelect.addEventListener("change", async () => {
            financeiroPage.empresaId = empresaSelect.value || "";
            financeiroPage.paginacao.lancamentos.paginaAtual = 1;
            financeiroPage.paginacao.fechamentos.paginaAtual = 1;
            popularEmpresasFinanceiro();
            await carregarFinanceiroTudo();
        });
    }

    if (periodoSelect) {
        periodoSelect.addEventListener("change", async () => {
            financeiroPage.periodoDias = periodoSelect.value || "30";
            if (financeiroNeedsDashboard()) {
                await carregarDashboardFinanceiro();
            }
        });
    }

    if (tipoSelect) {
        tipoSelect.addEventListener("change", async () => {
            financeiroPage.tipoLancamento = tipoSelect.value || "";
            financeiroPage.paginacao.lancamentos.paginaAtual = 1;
            if (financeiroNeedsLancamentos()) {
                await carregarLancamentosFinanceiro();
            }
        });
    }

    if (launchTipo) {
        launchTipo.addEventListener("change", () => {
            popularCategoriasFinanceiro();
        });
    }
}

function bindFinanceiroActions() {
    const openLaunch = document.getElementById("financeiro-open-launch");
    const openCloseout = document.getElementById("financeiro-open-closeout");
    const printFlow = document.getElementById("financeiro-print-flow");
    const printSales = document.getElementById("financeiro-print-sales");
    const launchForm = document.getElementById("financeiro-launch-form");
    const closeoutForm = document.getElementById("financeiro-closeout-form");

    if (openLaunch) {
        openLaunch.addEventListener("click", () => {
            resetFinanceiroLaunchForm();
            abrirFinanceiroModal("financeiro-launch-modal");
        });
    }

    if (openCloseout) {
        openCloseout.addEventListener("click", () => {
            resetFinanceiroCloseoutForm();
            abrirFinanceiroModal("financeiro-closeout-modal");
        });
    }

    if (printFlow) {
        printFlow.addEventListener("click", () => {
            const intervalo = getFinanceiroReportRange();
            const url = new URL("/api/financeiro/relatorios/fluxo-caixa/impressao", window.location.origin);
            url.searchParams.set("data_inicio", intervalo.dataInicio);
            url.searchParams.set("data_fim", intervalo.dataFim);
            if (financeiroPage.empresaId) {
                url.searchParams.set("empresa_id", financeiroPage.empresaId);
            }
            window.open(url.toString(), "_blank", "noopener");
        });
    }

    if (printSales) {
        printSales.addEventListener("click", () => {
            const intervalo = getFinanceiroReportRange();
            const url = new URL("/api/financeiro/relatorios/produtos-mais-vendidos/impressao", window.location.origin);
            url.searchParams.set("data_inicio", intervalo.dataInicio);
            url.searchParams.set("data_fim", intervalo.dataFim);
            if (financeiroPage.empresaId) {
                url.searchParams.set("empresa_id", financeiroPage.empresaId);
            }
            window.open(url.toString(), "_blank", "noopener");
        });
    }

    if (launchForm) {
        launchForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                const payload = {
                    tipo: document.getElementById("financeiro-launch-tipo")?.value || "ENTRADA",
                    empresa_id: document.getElementById("financeiro-launch-empresa")?.value || "",
                    categoria_id: document.getElementById("financeiro-launch-categoria")?.value || "",
                    forma_pagamento_id: document.getElementById("financeiro-launch-forma")?.value || "",
                    descricao: (document.getElementById("financeiro-launch-descricao")?.value || "").trim(),
                    valor: normalizeFinanceiroMoney(document.getElementById("financeiro-launch-valor")?.value || "0"),
                    data_competencia: document.getElementById("financeiro-launch-data")?.value || "",
                    observacao: (document.getElementById("financeiro-launch-observacao")?.value || "").trim()
                };

                const result = await requestFinanceiroJson("/api/financeiro/lancamentos", {
                    method: "POST",
                    headers: getFinanceiroHeaders(true),
                    body: JSON.stringify(payload)
                });

                showFinanceiroMessage(result.message || "Lancamento registrado com sucesso.", "success");
                fecharFinanceiroModal("financeiro-launch-modal");
                await carregarFinanceiroTudo();
            } catch (error) {
                showFinanceiroMessage(error.message || "Erro ao registrar o lancamento.", "error");
            }
        });
    }

    if (closeoutForm) {
        closeoutForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                const payload = {
                    empresa_id: document.getElementById("financeiro-closeout-empresa")?.value || "",
                    data_fechamento: document.getElementById("financeiro-closeout-data")?.value || "",
                    valor_inicial: normalizeFinanceiroMoney(document.getElementById("financeiro-closeout-inicial")?.value || "0"),
                    valor_final: normalizeFinanceiroMoney(document.getElementById("financeiro-closeout-final")?.value || "0"),
                    observacao: (document.getElementById("financeiro-closeout-observacao")?.value || "").trim()
                };

                const result = await requestFinanceiroJson("/api/financeiro/fechamentos", {
                    method: "POST",
                    headers: getFinanceiroHeaders(true),
                    body: JSON.stringify(payload)
                });

                showFinanceiroMessage(result.message || "Fechamento registrado com sucesso.", "success");
                fecharFinanceiroModal("financeiro-closeout-modal");
                await carregarFinanceiroTudo();
            } catch (error) {
                showFinanceiroMessage(error.message || "Erro ao registrar o fechamento.", "error");
            }
        });
    }
}

function bindFinanceiroMasks() {
    bindFinanceiroMoneyMask("financeiro-launch-valor");
    bindFinanceiroMoneyMask("financeiro-closeout-inicial");
    bindFinanceiroMoneyMask("financeiro-closeout-final");
}

function popularEmpresasFinanceiro() {
    const selects = [
        document.getElementById("financeiro-empresa"),
        document.getElementById("financeiro-launch-empresa"),
        document.getElementById("financeiro-closeout-empresa")
    ];

    selects.forEach((select, index) => {
        if (!select) return;
        const allowAll = index === 0;
        select.innerHTML = allowAll ? `<option value="">Todas as empresas</option>` : "";

        financeiroPage.auxiliares.empresas.forEach((empresa) => {
            const option = document.createElement("option");
            option.value = empresa.id;
            option.textContent = empresa.nome;
            option.selected = String(empresa.id) === String(financeiroPage.empresaId);
            select.appendChild(option);
        });
    });
}

function popularSelectsFinanceiro() {
    const formaSelect = document.getElementById("financeiro-launch-forma");
    if (formaSelect) {
        formaSelect.innerHTML = "";
        financeiroPage.auxiliares.formas_pagamento.forEach((forma) => {
            const option = document.createElement("option");
            option.value = forma.id;
            option.textContent = forma.nome;
            formaSelect.appendChild(option);
        });
    }

    popularCategoriasFinanceiro();
    resetFinanceiroLaunchForm();
    resetFinanceiroCloseoutForm();
}

function popularCategoriasFinanceiro() {
    const tipo = document.getElementById("financeiro-launch-tipo")?.value || "ENTRADA";
    const categoriaSelect = document.getElementById("financeiro-launch-categoria");
    if (!categoriaSelect) return;

    categoriaSelect.innerHTML = "";
    (financeiroPage.auxiliares.categorias?.[tipo] || []).forEach((categoria) => {
        const option = document.createElement("option");
        option.value = categoria.id;
        option.textContent = categoria.nome;
        categoriaSelect.appendChild(option);
    });
}

function renderDashboardFinanceiro() {
    const dashboard = financeiroPage.dashboard;
    if (!dashboard) return;

    setFinanceiroText("financeiro-kpi-entradas", formatFinanceiroCurrency(dashboard.kpis.entradas));
    setFinanceiroText("financeiro-kpi-saidas", formatFinanceiroCurrency(dashboard.kpis.saidas));
    setFinanceiroText("financeiro-kpi-saldo", formatFinanceiroCurrency(dashboard.kpis.saldo));
    setFinanceiroText("financeiro-kpi-faturamento", formatFinanceiroCurrency(dashboard.kpis.faturamento));
    setFinanceiroText("financeiro-kpi-ticket", formatFinanceiroCurrency(dashboard.kpis.ticket_medio));
    setFinanceiroText("financeiro-kpi-valor-estoque", formatFinanceiroCurrency(dashboard.kpis.valor_estoque));
    setFinanceiroText("financeiro-kpi-lucro-bruto", formatFinanceiroCurrency(dashboard.kpis.lucro_bruto));
    setFinanceiroText("financeiro-kpi-necessidade-compra", formatFinanceiroCurrency(dashboard.kpis.necessidade_compra));
    setFinanceiroText("financeiro-kpi-margem-bruta", `${formatFinanceiroPercent(dashboard.kpis.margem_bruta)} no periodo`);

    renderFinanceiroSerie(dashboard.serie_diaria || []);
    renderFinanceiroStack("financeiro-formas-list", dashboard.formas_pagamento || [], "forma_nome");
    renderFinanceiroStack("financeiro-categorias-list", dashboard.categorias_top || [], "categoria_nome", true);
    renderFinanceiroMensal(dashboard.mensal_resumo || []);
    renderFinanceiroProjecoes(dashboard.projecoes || []);
    renderFinanceiroRecomendacoes(dashboard.recomendacoes_compra || []);

    const caixaHoje = document.getElementById("financeiro-caixa-hoje");
    if (caixaHoje) {
        caixaHoje.innerHTML = `
            <strong class="block text-white">Resumo do caixa em dinheiro</strong>
            <div class="mt-4 space-y-2 text-sm text-slate-300">
                <div class="flex items-center justify-between gap-3">
                    <span>Entradas</span>
                    <strong>${formatFinanceiroCurrency(dashboard.caixa_hoje.entradas_dinheiro)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Saidas</span>
                    <strong>${formatFinanceiroCurrency(dashboard.caixa_hoje.saidas_dinheiro)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Saldo do dia</span>
                    <strong>${formatFinanceiroCurrency(dashboard.caixa_hoje.saldo_dinheiro)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3 border-t border-slate-800 pt-2 mt-2">
                    <span>Saldo esperado</span>
                    <strong>${formatFinanceiroCurrency(dashboard.caixa_hoje.saldo_esperado)}</strong>
                </div>
            </div>
        `;
    }
}

function renderFinanceiroMensal(items) {
    const container = document.getElementById("financeiro-mensal-list");
    if (!container) return;

    if (!items.length) {
        container.innerHTML = `<p class="text-slate-400">Sem consolidado mensal para o periodo selecionado.</p>`;
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="financeiro-stack-item">
            <div>
                <p class="font-medium text-white">${escapeFinanceiroHtml(formatCompetencia(item.competencia))}</p>
                <p class="text-xs text-slate-500 mt-1">
                    Entradas ${formatFinanceiroCurrency(item.entradas)} · Saidas ${formatFinanceiroCurrency(item.saidas)}
                </p>
            </div>
            <strong class="text-white">${formatFinanceiroCurrency(item.saldo)}</strong>
        </div>
    `).join("");
}

function renderFinanceiroProjecoes(items) {
    const container = document.getElementById("financeiro-projecoes-list");
    if (!container) return;

    if (!items.length) {
        container.innerHTML = `<p class="text-slate-400">Sem dados suficientes para projecao.</p>`;
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="financeiro-stack-item">
            <div>
                <p class="font-medium text-white">${escapeFinanceiroHtml(String(item.dias || 0))} dias</p>
                <p class="text-xs text-slate-500 mt-1">Media diaria ${formatFinanceiroCurrency(item.saldo_medio_diario)}</p>
            </div>
            <div class="text-right">
                <strong class="block text-white">${formatFinanceiroCurrency(item.saldo_projetado)}</strong>
                <span class="text-xs text-slate-500">${formatFinanceiroCurrency(item.variacao_prevista)}</span>
            </div>
        </div>
    `).join("");
}

function renderFinanceiroRecomendacoes(items) {
    const container = document.getElementById("financeiro-recomendacoes-list");
    if (!container) return;

    if (!items.length) {
        container.innerHTML = `<p class="text-slate-400">Nenhuma recomendacao de compra para o periodo.</p>`;
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="financeiro-stack-item">
            <div>
                <p class="font-medium text-white">${escapeFinanceiroHtml(item.produto_nome || "-")}</p>
                <p class="text-xs text-slate-500 mt-1">
                    Vendido ${escapeFinanceiroHtml(String(item.quantidade_vendida || 0))} · Cobertura ${escapeFinanceiroHtml(String(item.cobertura_dias || "0"))} dia(s)
                </p>
            </div>
            <div class="text-right">
                <strong class="block text-white">${escapeFinanceiroHtml(String(item.quantidade_sugerida || 0))} un.</strong>
                <span class="text-xs text-slate-500">${formatFinanceiroCurrency(item.valor_compra_sugerido)}</span>
            </div>
        </div>
    `).join("");
}

function renderFinanceiroSerie(items) {
    const container = document.getElementById("financeiro-serie-list");
    if (!container) return;

    if (!items.length) {
        container.innerHTML = `<p class="text-slate-400">Sem movimentacoes no periodo selecionado.</p>`;
        return;
    }

    const maxValue = items.reduce((max, item) => {
        return Math.max(max, parseFinanceiroMoney(item.entradas), parseFinanceiroMoney(item.saidas));
    }, 0) || 1;

    container.innerHTML = items.map((item) => {
        const entradas = parseFinanceiroMoney(item.entradas);
        const saidas = parseFinanceiroMoney(item.saidas);
        const larguraEntradas = Math.max((entradas / maxValue) * 100, 2);
        const larguraSaidas = Math.max((saidas / maxValue) * 100, 2);

        return `
            <div class="financeiro-series-row">
                <span class="text-sm text-slate-400">${formatFinanceiroDate(item.data)}</span>
                <div class="financeiro-bar-track">
                    <span class="financeiro-bar-entry" style="width:${larguraEntradas}%"></span>
                    <span class="financeiro-bar-exit" style="width:${larguraSaidas}%"></span>
                </div>
                <div class="text-right text-sm text-slate-300">
                    <strong class="block">${formatFinanceiroCurrency(item.entradas)}</strong>
                    <span class="text-slate-500">${formatFinanceiroCurrency(item.saidas)}</span>
                </div>
            </div>
        `;
    }).join("");
}

function renderFinanceiroStack(containerId, items, labelKey, showType = false) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!items.length) {
        container.innerHTML = `<p class="text-slate-400">Sem dados para o periodo selecionado.</p>`;
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="financeiro-stack-item">
            <div>
                <p class="font-medium text-white">${escapeFinanceiroHtml(item[labelKey] || "-")}</p>
                ${showType ? `<p class="text-xs text-slate-500 uppercase tracking-[0.14em] mt-1">${escapeFinanceiroHtml(item.tipo || "-")}</p>` : ""}
            </div>
            <strong class="text-white">${formatFinanceiroCurrency(item.valor)}</strong>
        </div>
    `).join("");
}

function renderLancamentosFinanceiro() {
    const body = document.getElementById("financeiro-lancamentos-body");
    if (!body) return;
    const paginacao = financeiroPage.paginacao.lancamentos;

    if (!financeiroPage.lancamentos.length) {
        body.innerHTML = `
            <tr>
                <td colspan="6" class="px-5 py-8 text-center text-slate-400">Nenhum lancamento encontrado.</td>
            </tr>
        `;
        renderFinanceiroPagination("financeiro-lancamentos-pagination", paginacao, 0, () => renderLancamentosFinanceiro());
        return;
    }

    const itensPagina = getFinanceiroPageItems(financeiroPage.lancamentos, paginacao);

    body.innerHTML = itensPagina.map((item) => `
        <tr class="hover:bg-slate-800/40 transition">
            <td class="px-5 py-4 align-middle text-slate-300">${formatFinanceiroDateTime(item.data_lancamento)}</td>
            <td class="px-5 py-4 align-middle">
                <p class="font-medium text-white">${escapeFinanceiroHtml(item.descricao || "-")}</p>
                <p class="text-xs text-slate-500">${escapeFinanceiroHtml(item.empresa_nome || "-")}</p>
            </td>
            <td class="px-5 py-4 align-middle text-slate-300">${escapeFinanceiroHtml(item.categoria_nome || "-")}</td>
            <td class="px-5 py-4 align-middle text-slate-300">${escapeFinanceiroHtml(item.forma_pagamento_nome || "-")}</td>
            <td class="px-5 py-4 align-middle">
                <span class="inline-flex items-center rounded-full ${item.origem === "PDV" ? "bg-sky-500/10 border border-sky-500/20 text-sky-300" : "bg-slate-700/40 border border-slate-700 text-slate-300"} px-2.5 py-1 text-[11px] font-medium">
                    ${escapeFinanceiroHtml(item.origem || "-")}
                </span>
            </td>
            <td class="px-5 py-4 align-middle text-right font-semibold ${item.tipo === "SAIDA" ? "text-rose-300" : "text-emerald-300"}">
                ${formatFinanceiroCurrency(item.valor)}
            </td>
        </tr>
    `).join("");

    renderFinanceiroPagination(
        "financeiro-lancamentos-pagination",
        paginacao,
        financeiroPage.lancamentos.length,
        () => renderLancamentosFinanceiro()
    );
}

function renderFechamentosFinanceiro() {
    const container = document.getElementById("financeiro-fechamentos-body");
    if (!container) return;
    const paginacao = financeiroPage.paginacao.fechamentos;

    if (!financeiroPage.fechamentos.length) {
        container.innerHTML = `<p class="text-slate-400 px-1">Nenhum fechamento registrado ainda.</p>`;
        renderFinanceiroPagination("financeiro-fechamentos-pagination", paginacao, 0, () => renderFechamentosFinanceiro());
        return;
    }

    const itensPagina = getFinanceiroPageItems(financeiroPage.fechamentos, paginacao);

    container.innerHTML = itensPagina.map((item) => `
        <article class="financeiro-closure-card">
            <div class="flex items-start justify-between gap-4">
                <div>
                    <p class="font-semibold text-white">${escapeFinanceiroHtml(item.empresa_nome || "-")}</p>
                    <p class="text-sm text-slate-400">${formatFinanceiroDate(item.data_fechamento)} - ${escapeFinanceiroHtml(item.funcionario_nome || "-")}</p>
                </div>
                <span class="text-xs uppercase tracking-[0.14em] text-slate-500">Caixa</span>
            </div>
            <div class="mt-4 space-y-2 text-sm text-slate-300">
                <div class="flex items-center justify-between gap-3">
                    <span>Inicial</span>
                    <strong>${formatFinanceiroCurrency(item.valor_inicial)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Final contado</span>
                    <strong>${formatFinanceiroCurrency(item.valor_final)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Sistema</span>
                    <strong>${formatFinanceiroCurrency(item.valor_sistema)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3 border-t border-slate-800 pt-2 mt-2">
                    <span>Diferenca</span>
                    <strong class="${parseFinanceiroMoney(item.diferenca) < 0 ? "text-rose-300" : "text-emerald-300"}">${formatFinanceiroCurrency(item.diferenca)}</strong>
                </div>
            </div>
        </article>
    `).join("");

    renderFinanceiroPagination(
        "financeiro-fechamentos-pagination",
        paginacao,
        financeiroPage.fechamentos.length,
        () => renderFechamentosFinanceiro()
    );
}

function resetFinanceiroLaunchForm() {
    const empresaSelect = document.getElementById("financeiro-launch-empresa");
    const tipoSelect = document.getElementById("financeiro-launch-tipo");
    const valorInput = document.getElementById("financeiro-launch-valor");
    const dataInput = document.getElementById("financeiro-launch-data");
    const descricao = document.getElementById("financeiro-launch-descricao");
    const observacao = document.getElementById("financeiro-launch-observacao");

    if (empresaSelect) {
        empresaSelect.value = financeiroPage.empresaId || financeiroPage.auxiliares.empresas[0]?.id || "";
    }
    if (tipoSelect) tipoSelect.value = "ENTRADA";
    if (valorInput) valorInput.value = "0,00";
    if (dataInput) dataInput.value = "";
    if (descricao) descricao.value = "";
    if (observacao) observacao.value = "";
    popularCategoriasFinanceiro();
}

function resetFinanceiroCloseoutForm() {
    const empresaSelect = document.getElementById("financeiro-closeout-empresa");
    const dataInput = document.getElementById("financeiro-closeout-data");
    const inicialInput = document.getElementById("financeiro-closeout-inicial");
    const finalInput = document.getElementById("financeiro-closeout-final");
    const observacao = document.getElementById("financeiro-closeout-observacao");

    if (empresaSelect) {
        empresaSelect.value = financeiroPage.empresaId || financeiroPage.auxiliares.empresas[0]?.id || "";
    }
    if (dataInput) dataInput.value = new Date().toISOString().slice(0, 10);
    if (inicialInput) inicialInput.value = "0,00";
    if (finalInput) finalInput.value = "0,00";
    if (observacao) observacao.value = "";
}

function getFinanceiroReportRange() {
    const periodo = Number(financeiroPage.periodoDias || "30");
    const dataFim = new Date();
    const dataInicio = new Date();
    dataInicio.setDate(dataFim.getDate() - Math.max(periodo - 1, 0));

    return {
        dataInicio: dataInicio.toISOString().slice(0, 10),
        dataFim: dataFim.toISOString().slice(0, 10)
    };
}

function requestFinanceiroJson(url, options = {}) {
    return fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            ...getFinanceiroHeaders(false),
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

function getFinanceiroHeaders(isJson = false) {
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

function bindFinanceiroModalClose() {
    document.addEventListener("click", (event) => {
        const closeTrigger = event.target.closest("[data-close-modal]");
        if (!closeTrigger) return;
        const modalId = closeTrigger.getAttribute("data-close-modal");
        if (modalId) {
            fecharFinanceiroModal(modalId);
        }
    });

    window.addEventListener("click", (event) => {
        if (event.target.classList.contains("modal-overlay")) {
            event.target.classList.add("hidden");
        }
    });
}

function abrirFinanceiroModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("hidden");
}

function fecharFinanceiroModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("hidden");
}

function showFinanceiroMessage(message, type = "success") {
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

function bindFinanceiroMoneyMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    window.DecimalInput?.bind(input, {
        decimals: 2,
        allowEmpty: false
    });
}

function getFinanceiroPageItems(items, paginacao) {
    const totalPaginas = Math.max(Math.ceil(items.length / paginacao.porPagina), 1);
    if (paginacao.paginaAtual > totalPaginas) {
        paginacao.paginaAtual = totalPaginas;
    }

    const inicio = (paginacao.paginaAtual - 1) * paginacao.porPagina;
    return items.slice(inicio, inicio + paginacao.porPagina);
}

function renderFinanceiroPagination(containerId, paginacao, totalItens, onChange) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const totalPaginas = Math.max(Math.ceil(totalItens / paginacao.porPagina), 1);

    if (!totalItens) {
        container.innerHTML = "";
        return;
    }

    if (totalPaginas <= 1) {
        container.innerHTML = `<div class="pagination-summary px-1 py-4">Exibindo ${totalItens} registro(s).</div>`;
        return;
    }

    const inicio = ((paginacao.paginaAtual - 1) * paginacao.porPagina) + 1;
    const fim = Math.min(paginacao.paginaAtual * paginacao.porPagina, totalItens);
    const paginas = buildFinanceiroPageNumbers(paginacao.paginaAtual, totalPaginas);

    container.innerHTML = `
        <div class="pagination-shell">
            <div class="pagination-summary">Exibindo ${inicio}-${fim} de ${totalItens} registros</div>
            <div class="pagination-controls">
                <button type="button" class="pagination-btn" data-page="${paginacao.paginaAtual - 1}" ${paginacao.paginaAtual === 1 ? "disabled" : ""}>Anterior</button>
                ${paginas.map((pagina) => pagina === "..."
                    ? `<span class="pagination-ellipsis">...</span>`
                    : `<button type="button" class="pagination-btn ${pagina === paginacao.paginaAtual ? "pagination-btn-active" : ""}" data-page="${pagina}">${pagina}</button>`
                ).join("")}
                <button type="button" class="pagination-btn" data-page="${paginacao.paginaAtual + 1}" ${paginacao.paginaAtual === totalPaginas ? "disabled" : ""}>Proxima</button>
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

function buildFinanceiroPageNumbers(paginaAtual, totalPaginas) {
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

function parseFinanceiroMoney(value) {
    return window.DecimalInput?.parse(value) ?? 0;
}

function formatFinanceiroMoneyInput(value) {
    return window.DecimalInput?.format(value, 2, {
        allowEmpty: false,
        useGrouping: true
    }) ?? "0,00";
}

function normalizeFinanceiroMoney(value) {
    return window.DecimalInput?.normalize(value, 2) ?? "0.00";
}

function formatFinanceiroCurrency(value) {
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    }).format(parseFinanceiroMoney(value));
}

function formatFinanceiroPercent(value) {
    const parsed = parseFinanceiroMoney(value);
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(parsed) + "%";
}

function formatFinanceiroDate(value) {
    if (!value) return "-";
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return "-";
    return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(date);
}

function formatFinanceiroDateTime(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";
    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short"
    }).format(date);
}

function formatCompetencia(value) {
    if (!value) return "-";
    const [ano, mes] = String(value).split("-");
    if (!ano || !mes) return value;

    const date = new Date(`${ano}-${mes}-01T00:00:00`);
    if (Number.isNaN(date.getTime())) return value;

    return new Intl.DateTimeFormat("pt-BR", {
        month: "long",
        year: "numeric"
    }).format(date);
}

function setFinanceiroText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function escapeFinanceiroHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
