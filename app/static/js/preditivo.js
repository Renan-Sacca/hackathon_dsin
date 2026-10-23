/**
 * PROMETHEUS — F.O.G.O. Cidade Preditiva Controller
 * Visualização e inteligência preditiva de trânsito e segurança urbana.
 */

let mapPreditivo = null;
let riskCirclesLayer = null;
let correlationLayer = null;
let predictedFailuresLayer = null;
let chartCustos = null;

let dadosRiscoRegioes = [];
let dadosCorrelacaoZonas = [];
let dadosPrevisoesFalhas = [];
let periodoAtivo = 'todos';

const MAP_CENTER = [-22.2139, -49.9458];
const DEFAULT_ZOOM = 13;

document.addEventListener('DOMContentLoaded', () => {
    initMapPreditivo();
    carregarDadosPreditivos();
});

// -------------------------------------------------------------------------
// 1. Inicialização do Mapa Preditivo
// -------------------------------------------------------------------------
function initMapPreditivo() {
    mapPreditivo = L.map('map-preditivo', {
        zoomControl: true,
        attributionControl: false
    }).setView(MAP_CENTER, DEFAULT_ZOOM);

    // Camada Base Dark
    const arcgisDark = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        className: 'dark-tiles',
        attribution: 'Map &copy; Esri'
    });
    arcgisDark.addTo(mapPreditivo);

    // Layer Groups
    riskCirclesLayer = L.layerGroup().addTo(mapPreditivo);
    correlationLayer = L.layerGroup().addTo(mapPreditivo);
    predictedFailuresLayer = L.layerGroup().addTo(mapPreditivo);

    // Layer Controls
    const overlays = {
        "<span style='color:#ef4444;font-weight:600;'><i class='bi bi-circle-fill me-1'></i>Círculos de Risco Urbano</span>": riskCirclesLayer,
        "<span style='color:#a78bfa;font-weight:600;'><i class='bi bi-diagram-3-fill me-1'></i>Zonas de Correlação de Falhas</span>": correlationLayer,
        "<span style='color:#fbbf24;font-weight:600;'><i class='bi bi-exclamation-triangle-fill me-1'></i>Falhas Iminentes Previstas</span>": predictedFailuresLayer,
    };
    L.control.layers(null, overlays, { position: 'topright', collapsed: false }).addTo(mapPreditivo);

    setTimeout(() => {
        mapPreditivo.invalidateSize();
    }, 250);
}

// -------------------------------------------------------------------------
// 2. Carregar Todos os Dados Preditivos
// -------------------------------------------------------------------------
async function carregarDadosPreditivos() {
    try {
        await Promise.all([
            carregarResumoKPIs(),
            carregarRiscoRegioes(),
            carregarPrevisoesFalha(),
            carregarRecomendaçõesReforco(),
            carregarAlertasPreventivos(),
            carregarCorrelacaoFalhas(),
            carregarProjecaoCustos(),
            carregarPrioridadeInstalacao(),
        ]);
    } catch (e) {
        console.error('Erro ao carregar dados preditivos:', e);
    }
}

// -------------------------------------------------------------------------
// 3. Resumo Executivo KPIs
// -------------------------------------------------------------------------
async function carregarResumoKPIs() {
    const data = await apiFetch('/api/preditivo/resumo');
    if (!data) return;

    document.getElementById('kpi-bairro-risco').textContent = data.bairro_maior_risco;
    document.getElementById('kpi-score-risco').textContent = data.score_maior_risco;
    document.getElementById('kpi-falhas-iminentes').textContent = data.total_equipamentos_em_risco;
    document.getElementById('kpi-alertas-preventivos').textContent = data.total_alertas_preventivos;
    document.getElementById('kpi-custo-30d').textContent = `R$ ${formatarMoeda(data.custo_projetado_30d)}`;
    document.getElementById('kpi-zonas-correlacao').textContent = data.zonas_correlacao_detectadas;
    document.getElementById('kpi-fila-instalacao').textContent = data.equipamentos_aguardando_instalacao;
}

// -------------------------------------------------------------------------
// 4. Risco por Região & Plotagem no Mapa (P3-PRED-01 / P3-TEST-01)
// -------------------------------------------------------------------------
async function carregarRiscoRegioes() {
    const data = await apiFetch('/api/preditivo/risco-regioes');
    if (!data) return;

    dadosRiscoRegioes = data;
    renderizarCirculosRisco();
}

function renderizarCirculosRisco() {
    if (!riskCirclesLayer) return;
    riskCirclesLayer.clearLayers();

    dadosRiscoRegioes.forEach(reg => {
        let score = reg.score_geral;
        if (periodoAtivo !== 'todos' && reg.detalhes_periodos[periodoAtivo]) {
            score = reg.detalhes_periodos[periodoAtivo].score_risco;
        }

        // Cor de acordo com o score
        let cor = '#10b981'; // verde
        if (score >= 70) cor = '#ef4444'; // vermelho
        else if (score >= 45) cor = '#f59e0b'; // laranja
        else if (score >= 25) cor = '#3b82f6'; // azul

        const circle = L.circle([reg.latitude, reg.longitude], {
            color: cor,
            fillColor: cor,
            fillOpacity: 0.35,
            radius: Math.max(300, score * 12),
            weight: 2
        });

        const popupContent = `
            <div style="min-width: 220px;">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge ${score >= 70 ? 'bg-danger' : score >= 45 ? 'bg-warning text-dark' : 'bg-success'}">
                        SCORE: ${score} / 100
                    </span>
                    <small class="text-muted">Período: ${periodoAtivo.toUpperCase()}</small>
                </div>
                <h6 class="fw-bold text-light mb-1 mt-2">${reg.bairro}</h6>
                <div class="small text-secondary mb-2">Pico mais crítico: <strong class="text-info">${reg.periodo_mais_critico.toUpperCase()}</strong></div>
                <div class="small text-muted mb-2">${reg.explicacao}</div>
                <div class="pt-2 border-top border-secondary border-opacity-25 text-end">
                    <button class="btn btn-outline-glass btn-sm py-0 px-2" style="font-size:0.75rem;" 
                        onclick="abrirModalExplicabilidade('Análise de Risco: ${reg.bairro}', 'Metodologia de Incidência Histórica', '${reg.explicacao}', 'Intensificar monitoramento no período da ${reg.periodo_mais_critico}.')">
                        <i class="bi bi-info-circle me-1"></i> Ver Análise
                    </button>
                </div>
            </div>
        `;

        circle.bindPopup(popupContent);
        riskCirclesLayer.addLayer(circle);
    });
}

function filtrarMapaPeriodo(periodo) {
    periodoAtivo = periodo;
    const links = document.querySelectorAll('#pills-periodo .nav-link');
    links.forEach(l => l.classList.remove('active'));
    event.target.classList.add('active');
    renderizarCirculosRisco();
}

// -------------------------------------------------------------------------
// 5. Previsão de Falhas de Equipamentos (MTBF) (P3-PRED-01 / P3-TEST-02)
// -------------------------------------------------------------------------
async function carregarPrevisoesFalha() {
    const data = await apiFetch('/api/preditivo/equipamentos-risco');
    const container = document.getElementById('container-previsoes-falha');
    if (!data || !container) return;

    dadosPrevisoesFalhas = data;

    if (data.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-muted small">Nenhum equipamento com padrão crítico de falha detectado.</div>';
        return;
    }

    // Renderizar markers no mapa para falhas iminentes
    if (predictedFailuresLayer) {
        predictedFailuresLayer.clearLayers();
        data.forEach(p => {
            if (p.probabilidade_falha_percentual >= 50 && p.latitude && p.longitude) {
                const icon = L.divIcon({
                    className: 'custom-div-icon',
                    html: `
                        <div class="custom-map-marker marker-mau_funcionamento marker-pulse-critical" style="width:28px;height:28px;font-size:13px;border-color:#fbbf24;">
                            <i class="bi bi-clock-history"></i>
                        </div>
                    `,
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                });
                const marker = L.marker([p.latitude, p.longitude], { icon });
                marker.bindPopup(`
                    <div style="min-width: 220px;">
                        <span class="badge bg-warning text-dark mb-1">FALHA IMINENTE: ${p.probabilidade_falha_percentual}%</span>
                        <h6 class="fw-bold text-light mb-1">${p.numero_serie}</h6>
                        <div class="small text-secondary mb-2">${p.tipo} • ${p.localizacao_bairro}</div>
                        <div class="small text-muted mb-2">Previsão: <strong>${formatarData(p.data_prevista_proxima_falha)}</strong> (em ~${p.dias_restantes} dias)</div>
                    </div>
                `);
                predictedFailuresLayer.addLayer(marker);
            }
        });
    }

    container.innerHTML = data.map(item => {
        let barColor = 'bg-success';
        if (item.probabilidade_falha_percentual >= 75) barColor = 'bg-danger';
        else if (item.probabilidade_falha_percentual >= 50) barColor = 'bg-warning';

        return `
            <div class="p-2 mb-2 rounded bg-dark border border-secondary border-opacity-25">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold text-light small">${item.numero_serie}</span>
                    <span class="badge ${item.probabilidade_falha_percentual >= 75 ? 'bg-danger' : 'bg-warning text-dark'}" style="font-size:0.7rem;">
                        ${item.probabilidade_falha_percentual}% RISCO
                    </span>
                </div>
                <div class="d-flex justify-content-between text-muted" style="font-size:0.75rem;">
                    <span>${item.tipo} • ${item.localizacao_bairro}</span>
                    <span>MTBF: ${item.mtbf_dias} dias</span>
                </div>
                <div class="progress my-2" style="height: 6px; background: rgba(255,255,255,0.06);">
                    <div class="progress-bar ${barColor}" style="width: ${item.probabilidade_falha_percentual}%;"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center" style="font-size:0.72rem;">
                    <span class="text-secondary">Prevista para: <strong class="text-light">${formatarData(item.data_prevista_proxima_falha)}</strong> (~${item.dias_restantes}d)</span>
                    <button class="btn btn-link btn-sm text-info p-0 text-decoration-none" 
                        onclick="abrirModalExplicabilidade('Previsão de Falha: ${item.numero_serie}', '${item.tipo} em ${item.localizacao_bairro}', '${item.explicacao}', 'Enviar equipe técnica para substituição de peças preventivamente em até ${item.dias_restantes} dias.')">
                        Explicabilidade &raquo;
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// -------------------------------------------------------------------------
// 6. Reforço de Agentes (P3-PRED-02)
// -------------------------------------------------------------------------
async function carregarRecomendaçõesReforco() {
    const data = await apiFetch('/api/preditivo/reforco-agentes');
    const container = document.getElementById('container-reforco-agentes');
    if (!data || !container) return;

    if (data.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-muted small">Nenhum déficit de efetivo identificado nas regiões.</div>';
        return;
    }

    container.innerHTML = data.slice(0, 6).map(r => {
        let badgeColor = r.prioridade === 'CRITICA' ? 'bg-danger' : r.prioridade === 'ALTA' ? 'bg-warning text-dark' : 'bg-primary';
        return `
            <div class="p-2 mb-2 rounded bg-dark border border-secondary border-opacity-25">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold text-light small">${r.bairro} (${r.periodo.toUpperCase()})</span>
                    <span class="badge ${badgeColor}" style="font-size:0.65rem;">${r.prioridade}</span>
                </div>
                <div class="small text-secondary mb-1">
                    Horário: <strong class="text-light">${r.horario_sugerido}</strong> • Risco: <span class="text-warning">${r.score_risco}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center small" style="font-size:0.75rem;">
                    <span class="text-muted">Presentes: <strong>${r.agentes_em_campo}</strong> | Ideal: <strong>${r.agentes_ideais}</strong></span>
                    <span class="text-info fw-bold">+${r.deficit_agentes} ${r.nome_tipo_sugerido}</span>
                </div>
                <div class="small text-muted mt-2 pt-1 border-top border-secondary border-opacity-10 fst-italic" style="font-size:0.7rem;">
                    ${r.justificativa}
                </div>
            </div>
        `;
    }).join('');
}

// -------------------------------------------------------------------------
// 7. Alertas Preventivos (P3-PRED-01 / P3-TEST-03)
// -------------------------------------------------------------------------
async function carregarAlertasPreventivos() {
    const data = await apiFetch('/api/preditivo/alertas-preventivos');
    const container = document.getElementById('container-alertas-preventivos');
    if (!data || !container) return;

    if (data.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-muted small">Nenhum alerta preventivo pendente.</div>';
        return;
    }

    container.innerHTML = data.map(a => {
        let borderClass = a.severidade === 'CRITICO' ? 'border-danger' : a.severidade === 'ALTO' ? 'border-warning' : 'border-info';
        let badgeClass = a.severidade === 'CRITICO' ? 'bg-danger' : a.severidade === 'ALTO' ? 'bg-warning text-dark' : 'bg-info text-dark';
        return `
            <div class="p-2 mb-2 rounded bg-dark border ${borderClass} border-opacity-50">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge ${badgeClass}" style="font-size:0.65rem;">${a.severidade}</span>
                    <small class="text-muted font-monospace">${a.numero_serie}</small>
                </div>
                <div class="small fw-bold text-light mb-1">${a.titulo}</div>
                <div class="small text-secondary mb-1" style="font-size:0.75rem;">${a.mensagem}</div>
                <div class="small text-info mt-1 pt-1 border-top border-secondary border-opacity-25" style="font-size:0.72rem;">
                    <i class="bi bi-lightbulb me-1"></i>${a.acao_recomendada}
                </div>
            </div>
        `;
    }).join('');
}

// -------------------------------------------------------------------------
// 8. Correlação de Falhas Compartilhadas (P3-PRED-04 / P3-TEST-06)
// -------------------------------------------------------------------------
async function carregarCorrelacaoFalhas() {
    const data = await apiFetch('/api/preditivo/correlacao-falhas');
    const container = document.getElementById('container-correlacoes');
    if (!data || !container) return;

    dadosCorrelacaoZonas = data;

    if (data.length === 0) {
        container.innerHTML = '<div class="col-12 text-center py-3 text-muted small">Nenhuma anomalia de correlação simultânea identificada.</div>';
        return;
    }

    // Renderizar no mapa com círculos de destaque roxos
    if (correlationLayer) {
        correlationLayer.clearLayers();
        data.forEach(z => {
            const circle = L.circle([z.latitude, z.longitude], {
                color: '#a78bfa',
                fillColor: '#8b5cf6',
                fillOpacity: 0.25,
                radius: z.raio_metros,
                weight: 2,
                dashArray: '6, 6'
            });

            circle.bindPopup(`
                <div style="min-width: 220px;">
                    <span class="badge bg-purple text-light mb-1" style="background:#8b5cf6;">CORRELAÇÃO: ${z.score_correlacao}%</span>
                    <h6 class="fw-bold text-light mb-1">Zona: ${z.bairro}</h6>
                    <div class="small text-warning mb-2"><i class="bi bi-exclamation-octagon me-1"></i>Causa Suspeita: ${z.causa_provavel}</div>
                    <div class="small text-muted mb-2">${z.total_equipamentos_afetados} equipamentos falharam juntos em ${z.total_episodios_simultaneos} episódios.</div>
                </div>
            `);
            correlationLayer.addLayer(circle);
        });
    }

    container.innerHTML = data.map(z => `
        <div class="col-md-12">
            <div class="correlacao-card">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold text-light">Zona ${z.bairro} — Ruas: ${z.ruas_principais.join(', ')}</span>
                    <span class="badge ${z.score_correlacao >= 70 ? 'bg-danger' : 'bg-purple'}" style="background:#8b5cf6;font-size:0.75rem;">
                        ${z.score_correlacao}% CORRELAÇÃO
                    </span>
                </div>
                <div class="small text-warning mb-2 fw-semibold">
                    <i class="bi bi-exclamation-triangle-fill me-1"></i>Causa Diagnosticada: ${z.causa_provavel}
                </div>
                <div class="small text-secondary mb-2">${z.explicacao}</div>
                <div class="d-flex flex-wrap gap-1 mt-2">
                    ${z.equipamentos.map(eq => `
                        <span class="badge bg-dark border border-secondary border-opacity-50 text-light small">
                            ${eq.numero_serie} (${eq.tipo})
                        </span>
                    `).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

// -------------------------------------------------------------------------
// 9. Projeção de Custo de Manutenção (P3-PRED-05 / P3-TEST-07)
// -------------------------------------------------------------------------
async function carregarProjecaoCustos() {
    const data = await apiFetch('/api/preditivo/custo-projecao');
    if (!data) return;

    document.getElementById('cost-proj-30').textContent = `R$ ${formatarMoeda(data.projecao_30_dias)}`;
    document.getElementById('cost-proj-60').textContent = `R$ ${formatarMoeda(data.projecao_60_dias)}`;
    document.getElementById('cost-proj-90').textContent = `R$ ${formatarMoeda(data.projecao_90_dias)}`;
    document.getElementById('cost-explanation').textContent = data.explicacao;

    // Renderizar gráfico Chart.js
    renderizarGraficoCustos(data.grafico_comparativo);
}

function renderizarGraficoCustos(grafico) {
    const ctx = document.getElementById('chart-custos-projecao')?.getContext('2d');
    if (!ctx) return;

    if (chartCustos) {
        chartCustos.destroy();
    }

    const allLabels = [...grafico.meses_reais, ...grafico.meses_projetados];
    const realValues = [...grafico.valores_reais, ...Array(grafico.meses_projetados.length).fill(null)];
    const projValues = [...Array(grafico.meses_reais.length).fill(null), ...grafico.valores_projetados];

    chartCustos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Custo Real Acumulado (R$)',
                    data: realValues,
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderColor: '#06b6d4',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Custo Projetado Preventivo (R$)',
                    data: projValues,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {
                                label += 'R$ ' + context.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(val) { return 'R$ ' + val.toLocaleString('pt-BR'); }
                    }
                }
            }
        }
    });
}

// -------------------------------------------------------------------------
// 10. Prioridade de Instalação de Equipamentos (P3-PRED-06 / P3-TEST-08)
// -------------------------------------------------------------------------
async function carregarPrioridadeInstalacao() {
    const data = await apiFetch('/api/preditivo/prioridade-instalacao');
    const container = document.getElementById('container-prioridade-instalacao');
    if (!data || !container) return;

    if (data.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-muted small">Nenhum equipamento aguardando instalação no momento.</div>';
        return;
    }

    container.innerHTML = data.map((item, idx) => {
        let badgeColor = item.nivel_urgencia === 'CRITICA' ? 'bg-danger' : item.nivel_urgencia === 'ALTA' ? 'bg-warning text-dark' : 'bg-info text-dark';
        return `
            <div class="prioridade-card">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-secondary font-monospace" style="font-size:0.8rem;">#${idx + 1}</span>
                        <h6 class="fw-bold text-light mb-0">${item.numero_serie}</h6>
                        <small class="text-muted">(${item.tipo} • ${item.marca})</small>
                    </div>
                    <span class="badge ${badgeColor}" style="font-size:0.75rem;">
                        SCORE ${item.score_urgencia} / 100 (${item.nivel_urgencia})
                    </span>
                </div>
                <div class="row align-items-center mt-2 pt-2 border-top border-secondary border-opacity-25" style="font-size:0.8rem;">
                    <div class="col-md-4 text-secondary">
                        <i class="bi bi-geo-alt text-info me-1"></i>Destino: <strong class="text-light">${item.bairro_destino}</strong>
                    </div>
                    <div class="col-md-4 text-secondary">
                        <i class="bi bi-hourglass-split text-warning me-1"></i>Espera: <strong class="text-light">${item.dias_espera} dias</strong>
                    </div>
                    <div class="col-md-4 text-secondary">
                        <i class="bi bi-shield-fill-exclamation text-danger me-1"></i>Risco Região: <strong class="text-light">${item.score_risco_bairro}/100</strong>
                    </div>
                </div>
                <div class="small text-muted mt-2 fst-italic" style="font-size:0.72rem;">
                    ${item.justificativa}
                </div>
            </div>
        `;
    }).join('');
}

// -------------------------------------------------------------------------
// 11. Modal de Explicabilidade (P3-TEST-05)
// -------------------------------------------------------------------------
function abrirModalExplicabilidade(titulo, subtitulo, explicacao, acao) {
    document.getElementById('modal-item-titulo').textContent = titulo;
    document.getElementById('modal-item-subtitulo').textContent = subtitulo;
    document.getElementById('modal-item-explicacao').textContent = explicacao;
    document.getElementById('modal-item-acao').textContent = acao;

    const modal = new bootstrap.Modal(document.getElementById('modalExplicabilidade'));
    modal.show();
}

function formatarMoeda(val) {
    if (!val && val !== 0) return '0,00';
    return Number(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatarData(dtStr) {
    if (!dtStr) return '--';
    const parts = dtStr.split('-');
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dtStr;
}
