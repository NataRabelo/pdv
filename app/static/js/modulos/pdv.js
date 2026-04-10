window.pdvPage = {
    auxiliares: { empresas: [], formas_pagamento: [], cupons: [] },
    produtos: [],
    catalogoPorId: {},
    catalogoPorCodigoBarras: {},
    vendas: [],
    carrinho: [],
    pagamentos: [],
    empresaId: "",
    busca: "",
    statusVenda: "",
    vendaSelecionada: null,
    payloadConfirmacaoPendente: null,
    ultimaVendaFinalizada: null,
    paymentCounter: 1
};

document.addEventListener("DOMContentLoaded", async () => {
    bindModalClose();
    bindPdvFilters();
    bindCartActions();
    bindSaleActions();
    bindMoneyMask("pdv-desconto-manual");

    await carregarAuxiliares();

    if (pdvPage.auxiliares.empresas.length === 1) {
        pdvPage.empresaId = String(pdvPage.auxiliares.empresas[0].id);
    }

    popularEmpresas();
    resetPayments();
    await carregarDadosPdv();
    if (pdvPage.empresaId) {
        document.getElementById("pdv-barcode-input")?.focus();
    }

    if (window.lucide) {
        lucide.createIcons();
    }
});

async function carregarAuxiliares() {
    const result = await requestJson("/api/pdv/auxiliares", { method: "GET" });
    pdvPage.auxiliares = result.data || pdvPage.auxiliares;
}

async function carregarDadosPdv() {
    await Promise.all([carregarProdutos(), carregarVendas()]);
}

async function carregarProdutos() {
    if (!pdvPage.empresaId) {
        pdvPage.produtos = [];
        limparCatalogoPdv();
        renderProdutos();
        atualizarKpis();
        return;
    }

    const url = new URL("/api/pdv/produtos", window.location.origin);
    url.searchParams.set("empresa_id", pdvPage.empresaId);
    if (pdvPage.busca) {
        url.searchParams.set("busca", pdvPage.busca);
    }

    const result = await requestJson(url.toString(), { method: "GET" });
    pdvPage.produtos = Array.isArray(result.data) ? result.data : [];
    reindexarCatalogoPdv(pdvPage.produtos);
    renderProdutos();
    atualizarKpis();
}

async function carregarVendas() {
    const url = new URL("/api/pdv/vendas", window.location.origin);
    url.searchParams.set("limite", "30");
    if (pdvPage.empresaId) {
        url.searchParams.set("empresa_id", pdvPage.empresaId);
    }
    if (pdvPage.statusVenda) {
        url.searchParams.set("status", pdvPage.statusVenda);
    }

    const result = await requestJson(url.toString(), { method: "GET" });
    pdvPage.vendas = Array.isArray(result.data) ? result.data : [];
    renderVendas();
    atualizarKpis();
}

function bindPdvFilters() {
    const empresaSelect = document.getElementById("pdv-empresa");
    const buscaInput = document.getElementById("pdv-busca");
    const barcodeInput = document.getElementById("pdv-barcode-input");
    const barcodeSubmit = document.getElementById("pdv-barcode-submit");
    const statusSelect = document.getElementById("pdv-status-venda");

    if (empresaSelect) {
        empresaSelect.addEventListener("change", async () => {
            pdvPage.empresaId = empresaSelect.value || "";
            limparCatalogoPdv();
            limparCarrinho();
            limparBarcodeField();
            popularEmpresas();
            await carregarDadosPdv();
            document.getElementById("pdv-barcode-input")?.focus();
        });
    }

    if (buscaInput) {
        buscaInput.addEventListener("input", async () => {
            pdvPage.busca = buscaInput.value || "";
            await carregarProdutos();
        });
    }

    if (barcodeInput) {
        barcodeInput.addEventListener("keydown", async (event) => {
            if (event.key !== "Enter") return;
            event.preventDefault();
            await adicionarProdutoPorCodigoDeBarras();
        });
    }

    if (barcodeSubmit) {
        barcodeSubmit.addEventListener("click", async () => {
            await adicionarProdutoPorCodigoDeBarras();
        });
    }

    if (statusSelect) {
        statusSelect.addEventListener("change", async () => {
            pdvPage.statusVenda = statusSelect.value || "";
            await carregarVendas();
        });
    }
}

function bindCartActions() {
    const clearCartBtn = document.getElementById("pdv-clear-cart");
    const addPaymentBtn = document.getElementById("pdv-add-payment");
    const cupomInput = document.getElementById("pdv-cupom-codigo");

    if (clearCartBtn) {
        clearCartBtn.addEventListener("click", () => {
            limparCarrinho();
            showMessage("Carrinho limpo.", "success");
        });
    }

    if (addPaymentBtn) {
        addPaymentBtn.addEventListener("click", () => {
            pdvPage.pagamentos.push(criarPagamentoVazio());
            renderPayments();
        });
    }

    if (cupomInput) {
        cupomInput.addEventListener("input", () => atualizarResumoVenda());
    }
}

function bindSaleActions() {
    const finalizeBtn = document.getElementById("pdv-finalizar-venda");
    const cancelBtn = document.getElementById("pdv-sale-cancel-button");
    const salePrintBtn = document.getElementById("pdv-sale-print-button");
    const confirmSubmitBtn = document.getElementById("pdv-confirm-submit");
    const successPrintBtn = document.getElementById("pdv-success-print");

    if (finalizeBtn) {
        finalizeBtn.addEventListener("click", () => {
            try {
                const payload = montarPayloadVenda();
                pdvPage.payloadConfirmacaoPendente = payload;
                abrirModalConfirmacaoVenda(payload);
            } catch (error) {
                showMessage(error.message || "Erro ao registrar a venda.", "error");
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", async () => {
            if (!pdvPage.vendaSelecionada || !pdvPage.vendaSelecionada.permite_cancelamento) {
                return;
            }

            try {
                const motivo = (document.getElementById("pdv-sale-cancel-reason")?.value || "").trim();
                const result = await requestJson(`/api/pdv/vendas/${pdvPage.vendaSelecionada.id}/cancelar`, {
                    method: "POST",
                    headers: getAuthHeaders(true),
                    body: JSON.stringify({ motivo })
                });

                showMessage(result.message || "Venda cancelada com sucesso.", "success");
                fecharModal("pdv-sale-modal");
                pdvPage.vendaSelecionada = null;
                await carregarDadosPdv();
            } catch (error) {
                showMessage(error.message || "Erro ao cancelar a venda.", "error");
            }
        });
    }

    if (salePrintBtn) {
        salePrintBtn.addEventListener("click", () => {
            if (!pdvPage.vendaSelecionada) return;
            abrirComprovanteVenda(pdvPage.vendaSelecionada.id);
        });
    }

    if (confirmSubmitBtn) {
        confirmSubmitBtn.addEventListener("click", async () => {
            if (!pdvPage.payloadConfirmacaoPendente) return;

            try {
                confirmSubmitBtn.disabled = true;
                const result = await requestJson("/api/pdv/vendas", {
                    method: "POST",
                    headers: getAuthHeaders(true),
                    body: JSON.stringify(pdvPage.payloadConfirmacaoPendente)
                });

                pdvPage.ultimaVendaFinalizada = result.data || null;
                pdvPage.payloadConfirmacaoPendente = null;
                fecharModal("pdv-confirm-modal");
                abrirModalSucessoVenda(pdvPage.ultimaVendaFinalizada);
                showMessage(result.message || "Venda registrada com sucesso.", "success");
                limparCarrinho();
                await carregarDadosPdv();
            } catch (error) {
                showMessage(error.message || "Erro ao registrar a venda.", "error");
            } finally {
                confirmSubmitBtn.disabled = false;
            }
        });
    }

    if (successPrintBtn) {
        successPrintBtn.addEventListener("click", () => {
            if (!pdvPage.ultimaVendaFinalizada?.id) return;
            abrirComprovanteVenda(pdvPage.ultimaVendaFinalizada.id);
        });
    }
}

function popularEmpresas() {
    const empresaSelect = document.getElementById("pdv-empresa");
    if (empresaSelect) {
        empresaSelect.innerHTML = `<option value="">Selecione a empresa</option>`;
        pdvPage.auxiliares.empresas.forEach((empresa) => {
            const option = document.createElement("option");
            option.value = empresa.id;
            option.textContent = empresa.nome;
            option.selected = String(empresa.id) === String(pdvPage.empresaId);
            empresaSelect.appendChild(option);
        });
    }

    const empresaInfo = document.getElementById("pdv-info-empresa");
    const empresaAtual = pdvPage.auxiliares.empresas.find((item) => String(item.id) === String(pdvPage.empresaId));
    if (empresaInfo) {
        empresaInfo.textContent = empresaAtual
            ? `Caixa pronto para atendimento em ${empresaAtual.nome}.`
            : "Escolha a empresa para liberar os produtos no caixa.";
    }

    setBarcodeFeedback(
        empresaAtual
            ? "Leitor pronto. Bip e Enter adicionam o item direto no carrinho."
            : "Selecione a empresa para habilitar a leitura por codigo de barras.",
        empresaAtual ? "info" : "muted"
    );
}

function renderProdutos() {
    const grid = document.getElementById("pdv-produtos-grid");
    if (!grid) return;

    if (!pdvPage.empresaId) {
        grid.innerHTML = `
            <article class="pdv-empty-state">
                <i data-lucide="shopping-bag" class="w-8 h-8"></i>
                <p>Selecione uma empresa para iniciar o PDV.</p>
            </article>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    if (!pdvPage.produtos.length) {
        grid.innerHTML = `
            <article class="pdv-empty-state">
                <i data-lucide="search-x" class="w-8 h-8"></i>
                <p>Nenhum produto encontrado para o filtro atual.</p>
            </article>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    grid.innerHTML = pdvPage.produtos.map((produto) => {
        const baixoEstoque = Number(produto.estoque_atual) <= Number(produto.estoque_minimo);
        const semEstoque = Number(produto.estoque_atual) <= 0;
        const badge = semEstoque
            ? `<span class="pdv-tag pdv-tag-danger">Sem estoque</span>`
            : baixoEstoque
                ? `<span class="pdv-tag pdv-tag-danger">Reposicao urgente</span>`
                : `<span class="pdv-tag pdv-tag-success">Disponivel</span>`;

        return `
            <article class="pdv-product-card">
                <div class="pdv-product-body">
                    <div class="flex items-start justify-between gap-3">
                        <div class="pdv-product-summary">
                            <div>
                                <h3 class="pdv-product-title">${escapeHtml(produto.nome || "-")}</h3>
                                <p class="pdv-product-description">${escapeHtml(produto.descricao || "Sem descricao cadastrada.")}</p>
                            </div>
                            <p class="pdv-product-code">
                                Codigo: ${escapeHtml(produto.codigo_barras || "Nao informado")}
                            </p>
                        </div>
                        ${badge}
                    </div>

                    <div class="pdv-product-meta">
                        <span class="pdv-tag pdv-tag-neutral">${escapeHtml(produto.categoria_nome || "Sem categoria")}</span>
                        <span class="pdv-tag pdv-tag-neutral">Estoque ${formatInteger(produto.estoque_atual)}</span>
                    </div>

                    <div class="pdv-product-footer">
                        <div>
                            <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Preco de venda</p>
                            <strong class="text-lg text-white">${formatCurrency(produto.valor_venda)}</strong>
                        </div>

                        <button type="button"
                            class="pdv-product-action inline-flex items-center gap-2 rounded-xl ${semEstoque ? "bg-slate-800 text-slate-500 cursor-not-allowed" : "bg-sky-500 hover:bg-sky-400 text-slate-950"} font-semibold px-4 py-3 transition"
                            ${semEstoque ? "disabled" : ""}
                            onclick="adicionarAoCarrinho(${produto.id})">
                            <i data-lucide="plus" class="w-4 h-4"></i>
                            Adicionar
                        </button>
                    </div>
                </div>
            </article>
        `;
    }).join("");

    if (window.lucide) {
        lucide.createIcons();
    }
}

function adicionarAoCarrinho(produtoId) {
    const produto = pdvPage.catalogoPorId[produtoId] || pdvPage.produtos.find((item) => Number(item.id) === Number(produtoId));
    if (!produto) {
        showMessage("Produto nao encontrado.", "error");
        return;
    }

    adicionarProdutoAoCarrinho(produto);
}

function adicionarProdutoAoCarrinho(produto) {
    const produtoId = Number(produto.id);
    const existente = pdvPage.carrinho.find((item) => Number(item.produto_id) === produtoId);
    if (existente) {
        if (existente.quantidade >= Number(produto.estoque_atual)) {
            showMessage("Nao ha estoque suficiente para aumentar a quantidade.", "error");
            return false;
        }
        existente.quantidade += 1;
    } else {
        if (Number(produto.estoque_atual) <= 0) {
            showMessage("Produto sem estoque disponivel.", "error");
            return false;
        }
        pdvPage.carrinho.push({
            produto_id: produtoId,
            nome: produto.nome,
            categoria_nome: produto.categoria_nome,
            valor_venda: produto.valor_venda,
            estoque_atual: Number(produto.estoque_atual),
            quantidade: 1
        });
    }

    renderCarrinho();
    return true;
}

async function adicionarProdutoPorCodigoDeBarras() {
    const input = document.getElementById("pdv-barcode-input");
    const codigo = normalizeBarcodeValue(input?.value || "");

    if (!pdvPage.empresaId) {
        showMessage("Selecione a empresa antes de usar o leitor.", "error");
        setBarcodeFeedback("Selecione a empresa para habilitar a leitura por codigo de barras.", "error");
        input?.focus();
        return;
    }

    if (!codigo) {
        setBarcodeFeedback("Leia um codigo valido para adicionar ao carrinho.", "muted");
        input?.focus();
        return;
    }

    try {
        setBarcodeFeedback("Buscando item no catalogo do caixa...", "info");
        let produto = pdvPage.catalogoPorCodigoBarras[codigo] || null;

        if (!produto) {
            const url = new URL("/api/pdv/produtos/codigo-barras", window.location.origin);
            url.searchParams.set("empresa_id", pdvPage.empresaId);
            url.searchParams.set("codigo_barras", codigo);
            const result = await requestJson(url.toString(), { method: "GET" });
            produto = result.data || null;
            if (produto) {
                reindexarCatalogoPdv([produto]);
            }
        }

        if (!produto) {
            throw new Error("Produto nao encontrado para o codigo de barras informado.");
        }

        const adicionado = adicionarProdutoAoCarrinho(produto);
        if (!adicionado) {
            setBarcodeFeedback("Produto localizado, mas sem saldo disponivel para nova inclusao.", "error");
            input?.focus();
            return;
        }

        if (input) {
            input.value = "";
            input.focus();
        }
        setBarcodeFeedback(`${produto.nome} adicionado ao carrinho.`, "success");
    } catch (error) {
        setBarcodeFeedback(error.message || "Nao foi possivel localizar o codigo de barras.", "error");
        showMessage(error.message || "Erro ao ler o codigo de barras.", "error");
        input?.focus();
    }
}

function alterarQuantidadeCarrinho(produtoId, delta) {
    const item = pdvPage.carrinho.find((row) => Number(row.produto_id) === Number(produtoId));
    if (!item) return;

    const novaQuantidade = item.quantidade + delta;
    if (novaQuantidade <= 0) {
        removerDoCarrinho(produtoId);
        return;
    }

    if (novaQuantidade > item.estoque_atual) {
        showMessage("Quantidade maior que o estoque disponivel.", "error");
        return;
    }

    item.quantidade = novaQuantidade;
    renderCarrinho();
}

function removerDoCarrinho(produtoId) {
    pdvPage.carrinho = pdvPage.carrinho.filter((item) => Number(item.produto_id) !== Number(produtoId));
    renderCarrinho();
}

function renderCarrinho() {
    const cartEmpty = document.getElementById("pdv-cart-empty");
    const cartItems = document.getElementById("pdv-cart-items");
    if (!cartEmpty || !cartItems) return;

    if (!pdvPage.carrinho.length) {
        cartEmpty.classList.remove("hidden");
        cartItems.classList.add("hidden");
        cartItems.innerHTML = "";
        resetPayments();
        atualizarResumoVenda();
        return;
    }

    cartEmpty.classList.add("hidden");
    cartItems.classList.remove("hidden");
    cartItems.innerHTML = pdvPage.carrinho.map((item) => `
        <article class="pdv-cart-item">
            <div>
                <p class="font-semibold text-white">${escapeHtml(item.nome)}</p>
                <p class="text-sm text-slate-400">${escapeHtml(item.categoria_nome || "Sem categoria")}</p>
                <p class="text-sm text-slate-500 mt-2">Unitario ${formatCurrency(item.valor_venda)}</p>
            </div>

            <div class="flex flex-col items-end gap-3">
                <button type="button"
                    class="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 hover:bg-rose-500/20 transition"
                    onclick="removerDoCarrinho(${item.produto_id})"
                    title="Remover item">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>

                <div class="pdv-cart-qty">
                    <button type="button" class="pdv-icon-btn" onclick="alterarQuantidadeCarrinho(${item.produto_id}, -1)">
                        <i data-lucide="minus" class="w-4 h-4"></i>
                    </button>
                    <strong class="min-w-[2rem] text-center text-white">${formatInteger(item.quantidade)}</strong>
                    <button type="button" class="pdv-icon-btn" onclick="alterarQuantidadeCarrinho(${item.produto_id}, 1)">
                        <i data-lucide="plus" class="w-4 h-4"></i>
                    </button>
                </div>

                <strong class="text-white">${formatCurrency(multiplicar(item.valor_venda, item.quantidade))}</strong>
            </div>
        </article>
    `).join("");

    atualizarResumoVenda();
    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderPayments() {
    const container = document.getElementById("pdv-payment-rows");
    if (!container) return;

    if (!pdvPage.pagamentos.length) {
        pdvPage.pagamentos.push(criarPagamentoVazio());
    }

    container.innerHTML = pdvPage.pagamentos.map((pagamento) => `
        <div class="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_10rem_3rem] gap-3 items-center">
            <select class="pdv-payment-forma w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 rounded-xl px-4 py-3 text-white outline-none transition"
                data-payment-uid="${pagamento.uid}">
                <option value="">Forma de pagamento</option>
                ${pdvPage.auxiliares.formas_pagamento.map((forma) => `
                    <option value="${forma.id}" ${String(forma.id) === String(pagamento.forma_pagamento_id) ? "selected" : ""}>
                        ${escapeHtml(forma.nome)}
                    </option>
                `).join("")}
            </select>

            <input type="text" inputmode="decimal"
                class="pdv-payment-valor w-full bg-slate-950 border border-slate-800 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 rounded-xl px-4 py-3 text-white outline-none transition"
                data-payment-uid="${pagamento.uid}"
                value="${pagamento.valor || ""}"
                placeholder="0,00">

            <button type="button"
                class="inline-flex items-center justify-center w-12 h-12 rounded-xl ${pdvPage.pagamentos.length === 1 ? "bg-slate-800 text-slate-600" : "bg-rose-500/10 border border-rose-500/20 text-rose-300 hover:bg-rose-500/20"} transition"
                ${pdvPage.pagamentos.length === 1 ? "disabled" : ""}
                data-remove-payment="${pagamento.uid}">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>
    `).join("");

    container.querySelectorAll(".pdv-payment-forma").forEach((select) => {
        select.addEventListener("change", () => {
            const payment = pdvPage.pagamentos.find((item) => String(item.uid) === String(select.dataset.paymentUid));
            if (!payment) return;
            payment.forma_pagamento_id = select.value || "";
        });
    });

    container.querySelectorAll(".pdv-payment-valor").forEach((input) => {
        bindMoneyMaskToElement(input);
        input.addEventListener("input", () => {
            const payment = pdvPage.pagamentos.find((item) => String(item.uid) === String(input.dataset.paymentUid));
            if (!payment) return;
            payment.valor = input.value;
            payment.touched = true;
        });
    });

    container.querySelectorAll("[data-remove-payment]").forEach((button) => {
        button.addEventListener("click", () => {
            pdvPage.pagamentos = pdvPage.pagamentos.filter((item) => String(item.uid) !== String(button.dataset.removePayment));
            renderPayments();
            atualizarResumoVenda();
        });
    });

    syncSinglePaymentWithTotal();

    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderVendas() {
    const body = document.getElementById("pdv-vendas-body");
    if (!body) return;

    if (!pdvPage.vendas.length) {
        body.innerHTML = `
            <tr>
                <td colspan="8" class="px-5 py-8 text-center text-slate-400">
                    Nenhuma venda encontrada para o filtro atual.
                </td>
            </tr>
        `;
        return;
    }

    body.innerHTML = pdvPage.vendas.map((venda) => {
        const pagamentos = venda.pagamentos.map((item) => item.forma_pagamento_nome).filter(Boolean).join(", ") || "-";
        const statusBadge = venda.status === "FINALIZADA"
            ? `<span class="inline-flex items-center rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-[11px] font-medium text-emerald-300">Finalizada</span>`
            : `<span class="inline-flex items-center rounded-full bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 text-[11px] font-medium text-rose-300">Cancelada</span>`;

        return `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="px-5 py-4 align-middle">
                    <p class="font-semibold text-white">${escapeHtml(venda.numero_unico)}</p>
                    <p class="text-xs text-slate-500">${escapeHtml(venda.funcionario_nome || "Sem operador")}</p>
                </td>
                <td class="px-5 py-4 align-middle text-slate-300">${formatDateTime(venda.data_venda)}</td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeHtml(venda.empresa_nome || "-")}</td>
                <td class="px-5 py-4 align-middle text-slate-300">${formatInteger(venda.itens_quantidade)}</td>
                <td class="px-5 py-4 align-middle text-slate-300">${escapeHtml(pagamentos)}</td>
                <td class="px-5 py-4 align-middle text-right text-white font-semibold">${formatCurrency(venda.total)}</td>
                <td class="px-5 py-4 align-middle text-center">${statusBadge}</td>
                <td class="px-5 py-4 align-middle">
                    <div class="flex items-center justify-center gap-2">
                        <button type="button"
                            class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-300 hover:bg-sky-500/20 transition"
                            onclick="abrirModalVenda(${venda.id}, false)">
                            <i data-lucide="file-text" class="w-4 h-4"></i>
                        </button>
                        <button type="button"
                            class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 hover:border-sky-500/30 hover:text-white transition"
                            onclick="abrirComprovanteVenda(${venda.id})">
                            <i data-lucide="printer" class="w-4 h-4"></i>
                        </button>
                        ${venda.permite_cancelamento ? `
                            <button type="button"
                                class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 hover:bg-rose-500/20 transition"
                                onclick="abrirModalVenda(${venda.id}, true)">
                                <i data-lucide="ban" class="w-4 h-4"></i>
                            </button>
                        ` : ""}
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    if (window.lucide) {
        lucide.createIcons();
    }
}

function abrirModalVenda(vendaId, focarCancelamento) {
    const venda = pdvPage.vendas.find((item) => Number(item.id) === Number(vendaId));
    if (!venda) return;

    pdvPage.vendaSelecionada = venda;

    const content = document.getElementById("pdv-sale-detail-content");
    const cancelReason = document.getElementById("pdv-sale-cancel-reason");
    const cancelButton = document.getElementById("pdv-sale-cancel-button");

    if (content) {
        content.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Venda</p>
                    <strong class="block text-white mt-2">${escapeHtml(venda.numero_unico)}</strong>
                    <p class="text-sm text-slate-400 mt-2">${escapeHtml(venda.empresa_nome || "-")}</p>
                    <p class="text-sm text-slate-400">${formatDateTime(venda.data_venda)}</p>
                </div>
                <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Resumo financeiro</p>
                    <strong class="block text-white mt-2">${formatCurrency(venda.total)}</strong>
                    <p class="text-sm text-slate-400 mt-2">Subtotal ${formatCurrency(venda.subtotal)}</p>
                    <p class="text-sm text-slate-400">Desconto ${formatCurrency(venda.desconto)}</p>
                </div>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500 mb-3">Itens</p>
                <div class="space-y-3">
                    ${venda.itens.map((item) => `
                        <div class="flex items-center justify-between gap-4">
                            <div>
                                <p class="font-medium text-white">${escapeHtml(item.produto_nome || "-")}</p>
                                <p class="text-sm text-slate-400">${formatInteger(item.quantidade)} x ${formatCurrency(item.valor_unitario)}</p>
                            </div>
                            <strong class="text-white">${formatCurrency(item.valor_total)}</strong>
                        </div>
                    `).join("")}
                </div>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500 mb-3">Pagamentos</p>
                <div class="space-y-3">
                    ${venda.pagamentos.map((pagamento) => `
                        <div class="flex items-center justify-between gap-4">
                            <div>
                                <p class="font-medium text-white">${escapeHtml(pagamento.forma_pagamento_nome || "-")}</p>
                                <p class="text-sm text-slate-400">${escapeHtml(pagamento.comprovante || "Sem comprovante")}</p>
                            </div>
                            <strong class="text-white">${formatCurrency(pagamento.valor)}</strong>
                        </div>
                    `).join("")}
                </div>
            </div>

            ${venda.observacao ? `
                <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                    <p class="text-xs uppercase tracking-[0.14em] text-slate-500 mb-2">Observacao</p>
                    <p class="text-sm text-slate-300 whitespace-pre-line">${escapeHtml(venda.observacao)}</p>
                </div>
            ` : ""}
        `;
    }

    if (cancelReason) {
        cancelReason.value = "";
    }

    if (cancelButton) {
        cancelButton.classList.toggle("hidden", !venda.permite_cancelamento);
    }

    abrirModal("pdv-sale-modal");
    if (focarCancelamento && cancelReason) {
        cancelReason.focus();
    }

    if (window.lucide) {
        lucide.createIcons();
    }
}

function abrirModalConfirmacaoVenda(payload) {
    const content = document.getElementById("pdv-confirm-content");
    if (!content) return;

    const subtotal = pdvPage.carrinho.reduce((sum, item) => sum + multiplicar(item.valor_venda, item.quantidade), 0);
    const desconto = parseCurrencyValue(document.getElementById("pdv-total-desconto")?.textContent || "0");
    const total = parseCurrencyValue(document.getElementById("pdv-total-geral")?.textContent || "0");
    const empresa = pdvPage.auxiliares.empresas.find((item) => String(item.id) === String(payload.empresa_id));

    content.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Empresa</p>
                <strong class="block text-white mt-2">${escapeHtml(empresa?.nome || "-")}</strong>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Itens</p>
                <strong class="block text-white mt-2">${formatInteger(payload.itens.length)}</strong>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Total</p>
                <strong class="block text-white mt-2">${formatCurrency(total)}</strong>
            </div>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
            <div class="flex items-center justify-between gap-4 mb-3">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500">Itens confirmados</p>
                <span class="text-sm text-slate-400">Subtotal ${formatCurrency(subtotal)} · Desconto ${formatCurrency(desconto)}</span>
            </div>
            <div class="space-y-3">
                ${pdvPage.carrinho.map((item) => `
                    <div class="flex items-center justify-between gap-4">
                        <div>
                            <p class="font-medium text-white">${escapeHtml(item.nome)}</p>
                            <p class="text-sm text-slate-400">${formatInteger(item.quantidade)} x ${formatCurrency(item.valor_venda)}</p>
                        </div>
                        <strong class="text-white">${formatCurrency(multiplicar(item.valor_venda, item.quantidade))}</strong>
                    </div>
                `).join("")}
            </div>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-slate-500 mb-3">Pagamentos</p>
            <div class="space-y-3">
                ${payload.pagamentos.map((pagamento) => {
                    const forma = pdvPage.auxiliares.formas_pagamento.find((item) => String(item.id) === String(pagamento.forma_pagamento_id));
                    return `
                        <div class="flex items-center justify-between gap-4">
                            <p class="font-medium text-white">${escapeHtml(forma?.nome || "-")}</p>
                            <strong class="text-white">${formatCurrency(pagamento.valor)}</strong>
                        </div>
                    `;
                }).join("")}
            </div>
        </div>
    `;

    abrirModal("pdv-confirm-modal");
    if (window.lucide) {
        lucide.createIcons();
    }
}

function abrirModalSucessoVenda(venda) {
    if (!venda) return;

    const message = document.getElementById("pdv-success-message");
    const summary = document.getElementById("pdv-success-summary");

    if (message) {
        message.textContent = `${venda.numero_unico} finalizada em ${formatCurrency(venda.total)}.`;
    }

    if (summary) {
        summary.innerHTML = `
            <div class="space-y-2 text-sm text-slate-300">
                <div class="flex items-center justify-between gap-3">
                    <span>Empresa</span>
                    <strong class="text-white">${escapeHtml(venda.empresa_nome || "-")}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Itens</span>
                    <strong class="text-white">${formatInteger(venda.itens_quantidade)}</strong>
                </div>
                <div class="flex items-center justify-between gap-3">
                    <span>Total</span>
                    <strong class="text-white">${formatCurrency(venda.total)}</strong>
                </div>
            </div>
        `;
    }

    abrirModal("pdv-success-modal");
}

function abrirComprovanteVenda(vendaId) {
    if (!vendaId) return;
    const url = new URL(`/api/pdv/vendas/${vendaId}/comprovante`, window.location.origin);
    window.open(url.toString(), "_blank", "noopener");
}

function atualizarKpis() {
    setText("pdv-kpi-produtos", String(pdvPage.produtos.length));
    setText(
        "pdv-kpi-baixo-estoque",
        String(pdvPage.produtos.filter((item) => Number(item.estoque_atual) <= Number(item.estoque_minimo)).length)
    );

    const hoje = new Date().toISOString().slice(0, 10);
    const vendasHoje = pdvPage.vendas.filter((item) => (item.data_venda || "").slice(0, 10) === hoje && item.status === "FINALIZADA");
    const totalHoje = vendasHoje.reduce((sum, item) => sum + parseCurrencyValue(item.total), 0);
    setText("pdv-kpi-vendas-hoje", String(vendasHoje.length));
    setText("pdv-kpi-faturamento", `${formatCurrency(totalHoje)} faturados hoje.`);
}

function montarPayloadVenda() {
    if (!pdvPage.empresaId) {
        throw new Error("Selecione a empresa antes de finalizar a venda.");
    }

    if (!pdvPage.carrinho.length) {
        throw new Error("Adicione pelo menos um item ao carrinho.");
    }

    const pagamentos = pdvPage.pagamentos
        .filter((item) => item.forma_pagamento_id && parseCurrencyValue(item.valor) > 0)
        .map((item) => ({
            forma_pagamento_id: item.forma_pagamento_id,
            valor: normalizeMoneyForApi(item.valor),
            comprovante: ""
        }));

    if (!pagamentos.length) {
        throw new Error("Informe ao menos um pagamento valido.");
    }

    return {
        empresa_id: pdvPage.empresaId,
        cupom_codigo: (document.getElementById("pdv-cupom-codigo")?.value || "").trim(),
        desconto_manual: normalizeMoneyForApi(document.getElementById("pdv-desconto-manual")?.value || "0"),
        observacao: (document.getElementById("pdv-observacao")?.value || "").trim(),
        itens: pdvPage.carrinho.map((item) => ({
            produto_id: item.produto_id,
            quantidade: item.quantidade,
            valor_unitario: String(parseCurrencyValue(item.valor_venda).toFixed(2))
        })),
        pagamentos
    };
}

function atualizarResumoVenda() {
    const subtotal = pdvPage.carrinho.reduce((sum, item) => sum + multiplicar(item.valor_venda, item.quantidade), 0);
    const descontoManual = parseCurrencyValue(document.getElementById("pdv-desconto-manual")?.value || "0");
    const cupom = obterCupomSelecionado();
    const descontoCupom = calcularDescontoCupom(cupom, subtotal);
    const descontoTotal = Math.min(subtotal, descontoManual + descontoCupom);
    const total = Math.max(subtotal - descontoTotal, 0);

    setText("pdv-total-subtotal", formatCurrency(subtotal));
    setText("pdv-total-desconto", formatCurrency(descontoTotal));
    setText("pdv-total-geral", formatCurrency(total));

    syncSinglePaymentWithTotal(total);
}

function obterCupomSelecionado() {
    const codigo = (document.getElementById("pdv-cupom-codigo")?.value || "").trim().toLowerCase();
    if (!codigo) return null;
    return (pdvPage.auxiliares.cupons || []).find((item) => String(item.codigo || "").toLowerCase() === codigo) || null;
}

function calcularDescontoCupom(cupom, subtotal) {
    if (!cupom) return 0;

    const valor = parseCurrencyValue(cupom.valor_desconto);
    if (cupom.tipo_desconto === "PERCENTUAL") {
        return subtotal * (valor / 100);
    }
    return Math.min(valor, subtotal);
}

function resetPayments() {
    pdvPage.pagamentos = [criarPagamentoVazio()];
    renderPayments();
}

function criarPagamentoVazio() {
    return {
        uid: pdvPage.paymentCounter++,
        forma_pagamento_id: "",
        valor: "",
        touched: false
    };
}

function syncSinglePaymentWithTotal(totalOverride) {
    if (pdvPage.pagamentos.length !== 1) return;

    const total = typeof totalOverride === "number"
        ? totalOverride
        : parseCurrencyValue(document.getElementById("pdv-total-geral")?.textContent || "0");
    const payment = pdvPage.pagamentos[0];

    if (!payment.touched || !payment.valor || parseCurrencyValue(payment.valor) === 0) {
        payment.valor = formatCurrencyInput(total);
        const input = document.querySelector(`.pdv-payment-valor[data-payment-uid="${payment.uid}"]`);
        if (input) {
            input.value = payment.valor;
        }
    }
}

function limparCarrinho() {
    pdvPage.carrinho = [];
    pdvPage.payloadConfirmacaoPendente = null;
    const cupom = document.getElementById("pdv-cupom-codigo");
    const desconto = document.getElementById("pdv-desconto-manual");
    const observacao = document.getElementById("pdv-observacao");
    if (cupom) cupom.value = "";
    if (desconto) desconto.value = "0,00";
    if (observacao) observacao.value = "";
    renderCarrinho();
}

function limparCatalogoPdv() {
    pdvPage.catalogoPorId = {};
    pdvPage.catalogoPorCodigoBarras = {};
}

function reindexarCatalogoPdv(produtos) {
    (produtos || []).forEach((produto) => {
        if (!produto || !produto.id) return;
        pdvPage.catalogoPorId[produto.id] = produto;

        const codigo = normalizeBarcodeValue(produto.codigo_barras);
        if (codigo) {
            pdvPage.catalogoPorCodigoBarras[codigo] = produto;
        }
    });
}

function normalizeBarcodeValue(value) {
    return String(value || "").replace(/\s+/g, "").trim();
}

function limparBarcodeField() {
    const input = document.getElementById("pdv-barcode-input");
    if (input) {
        input.value = "";
    }
}

function setBarcodeFeedback(message, type = "info") {
    const element = document.getElementById("pdv-barcode-feedback");
    if (!element) return;

    element.textContent = message;
    element.classList.remove("is-success", "is-error", "is-info", "is-muted");
    element.classList.add(`is-${type}`);
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
            result = { success: false, message: "Resposta invalida do servidor." };
        }

        if (!response.ok || result.success === false) {
            throw new Error(result.message || "Erro na requisicao.");
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

function bindMoneyMask(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    bindMoneyMaskToElement(input);
}

function bindMoneyMaskToElement(input) {
    if (!input) return;

    const isDiscountInput = input.id === "pdv-desconto-manual";

    window.DecimalInput?.bind(input, {
        decimals: 2,
        allowEmpty: !isDiscountInput,
        onInput: () => {
            if (isDiscountInput) {
                atualizarResumoVenda();
            }
        },
        onBlur: () => {
            if (isDiscountInput) {
                atualizarResumoVenda();
            }
        }
    });
}

function parseCurrencyValue(value) {
    return window.DecimalInput?.parse(value) ?? 0;
}

function formatCurrencyInput(value) {
    return window.DecimalInput?.format(value, 2, {
        allowEmpty: false,
        useGrouping: true
    }) ?? "0,00";
}

function normalizeMoneyForApi(value) {
    return window.DecimalInput?.normalize(value, 2) ?? "0.00";
}

function multiplicar(valor, quantidade) {
    return parseCurrencyValue(valor) * Number(quantidade || 0);
}

function formatCurrency(value) {
    const parsed = typeof value === "number" ? value : parseCurrencyValue(value);
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function formatInteger(value) {
    const digits = String(value ?? "").replace(/\D/g, "");
    const parsed = Number.parseInt(digits || "0", 10);
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(Number.isNaN(parsed) ? 0 : parsed);
}

function formatDateTime(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";

    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short"
    }).format(date);
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
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
