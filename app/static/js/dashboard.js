/**
 * PROMETHEUS — F.O.G.O. Dashboard & Map Controller
 * Implements interactive Leaflet mapping, marker clustering, heatmap, real-time filters and auto-refresh.
 */

let map = null;
let markersCluster = null;
let heatLayer = null;
let isHeatmapActive = false;
let autoRefreshTimer = null;
let autoRefreshInterval = 30; // seconds
let countdownSeconds = 30;
let isPaused = false;

// Cache of map markers by ID for instant focus
const equipmentMarkers = {};
const agentMarkers = {};

// Default Map Center: Marília, SP
const MAP_CENTER = [-22.2139, -49.9458];
const DEFAULT_ZOOM = 13;

// Equipment Icon SVGs by Type
const ICONS_SVG = {
    'radar_velocidade': '<i class="bi bi-speedometer2"></i>',
    'radar_semaforo': '<i class="bi bi-stoplights"></i>',
    'radar_conversao': '<i class="bi bi-sign-turn-left"></i>',
    'camera_monitoramento': '<i class="bi bi-camera-video"></i>',
    'balanca_caminhao': '<i class="bi bi-truck"></i>',
    'veiculo_fiscalizacao_estacionamento': '<i class="bi bi-car-front-fill"></i>',
    'cancela_automatizada': '<i class="bi bi-slash-square"></i>',
    'veiculo_transporte': '<i class="bi bi-bus-front"></i>',
    'totem_estacionamento': '<i class="bi bi-p-square"></i>',
    'patinete_eletrico': '<i class="bi bi-scooter"></i>',
    'moto_agente': '<i class="bi bi-bicycle"></i>',
    'viatura_guarda': '<i class="bi bi-shield-shaded"></i>',
    'viatura_policia': '<i class="bi bi-shield-fill-check"></i>',
    'outro': '<i class="bi bi-cpu"></i>'
};

const AGENT_ICONS_SVG = {
    'agente_transito': '<i class="bi bi-person-fill"></i>',
    'guarda_municipal': '<i class="bi bi-person-badge-fill"></i>',
    'policial_militar': '<i class="bi bi-person-vcard-fill"></i>'
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initFilters();
    loadDashboardData();
    startAutoRefresh();
});

function initMap() {
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView(MAP_CENTER, DEFAULT_ZOOM);

    // 100% Free Tile Layers (NO API Key required!)
    // 1. Cyber Dark Map (ArcGIS World Street Map with CSS Dark Filter)
    const arcgisDark = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        className: 'dark-tiles',
        attribution: 'Map &copy; Esri'
    });

    // 2. Clear Standard Urban Map (ArcGIS Street)
    const arcgisStandard = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Map &copy; Esri'
    });

    // 3. Real Satellite Map (Esri World Imagery)
    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Imagery &copy; Esri'
    });

    // 4. OpenStreetMap Standard
    const osmStandard = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    });

    // Default to Cyber Dark
    arcgisDark.addTo(map);

    // Layer switcher control (top-right)
    const baseLayers = {
        "<span style='color:#06b6d4;font-weight:600;'>Cyber Dark</span>": arcgisDark,
        "<span>Mapa Urbano (Claro)</span>": arcgisStandard,
        "<span>Satélite Real</span>": esriSatellite,
        "<span>OpenStreetMap</span>": osmStandard
    };
    L.control.layers(baseLayers, null, { position: 'topright' }).addTo(map);

    // Trigger map resize fix
    setTimeout(() => {
        map.invalidateSize();
    }, 200);

    // Initialize Marker Cluster Group
    // Note: disableClusteringAtZoom: 16 ensures that at street level (zoom 16+),
    // individual equipment markers are ALWAYS visible and never hidden inside unresolved clusters.
    markersCluster = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 40,
        disableClusteringAtZoom: 16,
        removeOutsideVisibleBounds: false,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            return L.divIcon({
                html: `<div class="d-flex align-items-center justify-content-center fw-bold text-dark rounded-circle shadow" style="background:#06b6d4; width:34px; height:34px; border:2px solid #fff; font-size:12px;">${count}</div>`,
                className: 'cluster-custom-icon',
                iconSize: L.point(34, 34)
            });
        }
    });

    map.addLayer(markersCluster);

    // Map controls: Toggle Heatmap button
    document.getElementById('btn-toggle-heat')?.addEventListener('click', toggleHeatmap);
    document.getElementById('btn-reset-map')?.addEventListener('click', () => {
        map.flyTo(MAP_CENTER, DEFAULT_ZOOM);
    });
}

// Create Custom Marker Icon
function createMarkerIcon(tipo, situacao, criticidade) {
    const iconHtml = ICONS_SVG[tipo] || ICONS_SVG['outro'];
    const pulseClass = criticidade === 'critico' ? 'marker-pulse-critical' : '';
    const situacaoClass = `marker-${situacao}`;

    return L.divIcon({
        className: 'custom-div-icon',
        html: `
            <div class="custom-map-marker ${situacaoClass} ${pulseClass}" style="width: 32px; height: 32px; font-size: 15px;">
                ${iconHtml}
            </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16]
    });
}

function createAgentIcon(tipo) {
    const iconHtml = AGENT_ICONS_SVG[tipo] || '<i class="bi bi-person-fill"></i>';
    let corClass = 'marker-agente-transito';
    if (tipo === 'guarda_municipal') corClass = 'marker-agente-guarda';
    if (tipo === 'policial_militar') corClass = 'marker-agente-pm';

    return L.divIcon({
        className: 'custom-div-icon',
        html: `
            <div class="custom-map-marker ${corClass}" style="width: 28px; height: 28px; font-size: 13px;">
                ${iconHtml}
            </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
    });
}

// Load All Dashboard Components
async function loadDashboardData() {
    updateRefreshBadge();
    await Promise.all([
        loadKPIs(),
        loadMapData(),
        loadAlerts(),
        loadRegionsHealth()
    ]);

    // Check if redirected from another page to focus on a specific equipment
    const urlParams = new URLSearchParams(window.location.search);
    const focoId = urlParams.get('foco_id');
    const lat = parseFloat(urlParams.get('lat'));
    const lon = parseFloat(urlParams.get('lon'));

    if (focoId && !isNaN(lat) && !isNaN(lon)) {
        setTimeout(() => {
            focarNoEquipamento(parseInt(focoId), lat, lon);
            // Clean query params from URL without refreshing
            window.history.replaceState({}, document.title, window.location.pathname);
        }, 500);
    }
}

// 1. KPIs
async function loadKPIs() {
    try {
        const kpis = await apiFetch('/api/dashboard/metricas');
        if (!kpis) return;

        document.getElementById('kpi-total').textContent = kpis.total_equipamentos;
        document.getElementById('kpi-operacionais').textContent = kpis.operacionais;
        document.getElementById('kpi-disponibilidade').textContent = `${kpis.percentual_disponibilidade}%`;
        document.getElementById('kpi-indisponiveis').textContent = kpis.indisponiveis;
        document.getElementById('kpi-manutencao-imediata').textContent = kpis.manutencao_imediata;
        document.getElementById('kpi-agentes').textContent = `${kpis.agentes_em_atividade} / ${kpis.total_agentes}`;
    } catch (e) {
        console.error('Erro ao carregar KPIs:', e);
    }
}

// 2. Map Data
async function loadMapData() {
    const tipo = document.getElementById('map-filter-tipo')?.value || '';
    const situacao = document.getElementById('map-filter-situacao')?.value || '';
    const bairro = document.getElementById('map-filter-bairro')?.value || '';
    const orgao = document.getElementById('map-filter-orgao')?.value || '';
    const busca = document.getElementById('map-filter-busca')?.value.trim() || '';

    const params = new URLSearchParams();
    if (tipo) params.append('tipo', tipo);
    if (situacao) params.append('situacao', situacao);
    if (bairro) params.append('bairro', bairro);
    if (orgao) params.append('orgao', orgao);
    if (busca) params.append('busca', busca);

    try {
        const data = await apiFetch(`/api/dashboard/mapa?${params.toString()}`);
        if (!data) return;

        markersCluster.clearLayers();
        Object.keys(equipmentMarkers).forEach(k => delete equipmentMarkers[k]);
        Object.keys(agentMarkers).forEach(k => delete agentMarkers[k]);

        const heatPoints = [];

        // Plot Equipamentos
        data.equipamentos.forEach(eq => {
            if (eq.latitude && eq.longitude) {
                const icon = createMarkerIcon(eq.tipo, eq.situacao, eq.criticidade);
                const marker = L.marker([eq.latitude, eq.longitude], { icon });

                // Popup content
                const popupContent = `
                    <div style="min-width: 220px;">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="badge-situacao badge-${eq.situacao.replace('_', '-')}">${eq.situacao.toUpperCase()}</span>
                            <small class="text-muted font-monospace">${eq.numero_serie}</small>
                        </div>
                        <h6 class="fw-bold text-light mb-1 mt-2">${formatarTipo(eq.tipo)}</h6>
                        <div class="text-secondary small mb-2">${eq.marca} • ${eq.modelo}</div>
                        <div class="small text-muted mb-2">
                            <i class="bi bi-geo-alt text-info me-1"></i>${eq.localizacao_rua}, ${eq.localizacao_bairro}
                        </div>
                        <div class="d-flex justify-content-between align-items-center pt-2 border-top border-secondary border-opacity-25 mt-2">
                            <small class="text-info">${eq.orgao_responsavel}</small>
                            <div class="d-flex gap-1">
                                <a href="/admin/equipamentos/${eq.id}/editar#historico" class="btn btn-outline-info btn-sm py-0 px-2" style="font-size:0.75rem;" title="Histórico de Manutenções">
                                    <i class="bi bi-clock-history"></i>
                                </a>
                                <a href="/admin/equipamentos/${eq.id}/editar" class="btn btn-cyan btn-sm py-0 px-2" style="font-size:0.75rem;">
                                    <i class="bi bi-pencil-square"></i> Editar
                                </a>
                            </div>
                        </div>
                    </div>
                `;
                marker.bindPopup(popupContent);
                markersCluster.addLayer(marker);
                equipmentMarkers[eq.id] = marker;

                // If critical, push to heatmap with high intensity
                if (eq.criticidade === 'critico') {
                    heatPoints.push([eq.latitude, eq.longitude, 1.0]);
                } else if (eq.criticidade === 'urgente') {
                    heatPoints.push([eq.latitude, eq.longitude, 0.6]);
                }
            }
        });

        // Plot Agentes
        data.agentes.forEach(ag => {
            if (ag.latitude && ag.longitude) {
                const icon = createAgentIcon(ag.tipo);
                const marker = L.marker([ag.latitude, ag.longitude], { icon });

                const popupContent = `
                    <div style="min-width: 200px;">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="badge bg-success bg-opacity-25 text-success border border-success border-opacity-50">AGENTE EM CAMPO</span>
                            <small class="text-muted font-monospace">${ag.matricula}</small>
                        </div>
                        <h6 class="fw-bold text-light mb-1 mt-2">${ag.nome}</h6>
                        <div class="text-secondary small mb-1">${formatarTipoAgente(ag.tipo)} • ${ag.orgao}</div>
                        <div class="small text-muted mb-2">
                            <i class="bi bi-telephone text-info me-1"></i>${ag.telefone || 'Rádio Operacional'}
                        </div>
                        <div class="pt-2 border-top border-secondary border-opacity-25 text-end">
                            <a href="/admin/agentes/${ag.id}/editar" class="btn btn-outline-glass btn-sm py-0 px-2" style="font-size:0.75rem;">
                                Editar Cadastro
                            </a>
                        </div>
                    </div>
                `;
                marker.bindPopup(popupContent);
                markersCluster.addLayer(marker);
                agentMarkers[ag.id] = marker;
            }
        });

        // Setup HeatLayer if L.heatLayer exists
        if (typeof L.heatLayer === 'function') {
            if (heatLayer) {
                map.removeLayer(heatLayer);
            }
            heatLayer = L.heatLayer(heatPoints, {
                radius: 35,
                blur: 20,
                maxZoom: 15,
                gradient: { 0.4: 'blue', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red' }
            });
            if (isHeatmapActive) {
                map.addLayer(heatLayer);
            }
        }
    } catch (e) {
        console.error('Erro ao carregar mapa:', e);
    }
}

// 3. Alerts Panel
async function loadAlerts() {
    try {
        const alerts = await apiFetch('/api/dashboard/alertas');
        const container = document.getElementById('alerts-container');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = `
                <div class="p-3 text-center text-muted small">
                    <i class="bi bi-check-circle text-success fs-4 d-block mb-1"></i>
                    Nenhum alerta crítico ativo no momento.
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(a => {
            let cardClass = 'alert-card-atencao';
            let icon = 'bi-info-circle text-primary';
            if (a.severidade === 'CRITICO') {
                cardClass = 'alert-card-critico';
                icon = 'bi-exclamation-triangle-fill text-danger';
            } else if (a.severidade === 'URGENTE') {
                cardClass = 'alert-card-urgente';
                icon = 'bi-exclamation-circle-fill text-warning';
            }

            return `
                <div class="alert-card-item ${cardClass}" onclick="focarNoEquipamento(${a.equipamento_id}, ${a.latitude}, ${a.longitude})">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge ${a.severidade === 'CRITICO' ? 'bg-danger' : a.severidade === 'URGENTE' ? 'bg-warning text-dark' : 'bg-primary'} font-monospace" style="font-size:0.65rem;">
                            ${a.severidade}
                        </span>
                        <small class="text-muted font-monospace">${a.numero_serie}</small>
                    </div>
                    <div class="small text-light fw-semibold mb-1">${a.mensagem}</div>
                    <div class="d-flex justify-content-between text-muted" style="font-size:0.75rem;">
                        <span><i class="bi bi-geo-alt me-1"></i>${a.bairro}</span>
                        <span class="text-info"><i class="bi bi-crosshair me-1"></i>Focar</span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Erro ao carregar alertas:', e);
    }
}

// 4. Regions Health
async function loadRegionsHealth() {
    try {
        const regions = await apiFetch('/api/dashboard/regioes');
        const container = document.getElementById('regions-container');
        if (!container) return;

        if (!regions || regions.length === 0) {
            container.innerHTML = '<div class="p-2 text-muted small">Nenhuma região computada.</div>';
            return;
        }

        container.innerHTML = regions.map(r => {
            let color = 'bg-success';
            if (r.percentual_saude < 60) color = 'bg-danger';
            else if (r.percentual_saude < 85) color = 'bg-warning';

            return `
                <div class="region-item" onclick="filtrarPorRegiao('${r.bairro}', ${r.lat}, ${r.lon})">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-semibold text-light small">${r.bairro}</span>
                        <span class="small fw-bold text-light">${r.percentual_saude}%</span>
                    </div>
                    <div class="progress progress-health mb-1">
                        <div class="progress-bar ${color}" style="width: ${r.percentual_saude}%;"></div>
                    </div>
                    <div class="d-flex justify-content-between text-muted" style="font-size: 0.72rem;">
                        <span>${r.operacionais} de ${r.total} operacionais</span>
                        ${r.problemas > 0 ? `<span class="text-danger fw-bold"><i class="bi bi-exclamation-circle me-1"></i>${r.problemas} falha(s)</span>` : '<span class="text-success">Estável</span>'}
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Erro ao carregar regiões:', e);
    }
}

// Click to focus marker on map
function focarNoEquipamento(id, lat, lon) {
    if (!map || !lat || !lon) return;

    // Smooth scroll viewport to center the map on screen
    const mapEl = document.getElementById('map');
    if (mapEl) {
        mapEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    const targetZoom = 17;
    const marker = equipmentMarkers[id];

    const openMarker = () => {
        if (marker) {
            marker.openPopup();
        }
    };

    const currentCenter = map.getCenter();
    const currentZoom = map.getZoom();
    const isAtLocation = currentZoom === targetZoom &&
        Math.abs(currentCenter.lat - lat) < 0.0001 &&
        Math.abs(currentCenter.lng - lon) < 0.0001;

    if (isAtLocation) {
        openMarker();
        return;
    }

    // Set one-time listener when flying finishes to open popup
    let moveEndFired = false;
    const onMoveEnd = () => {
        if (moveEndFired) return;
        moveEndFired = true;
        setTimeout(openMarker, 100);
    };

    map.once('moveend', onMoveEnd);

    // Safety timeout in case flyTo animation is skipped or interrupted
    setTimeout(() => {
        if (!moveEndFired) {
            onMoveEnd();
        }
    }, 1200);

    map.flyTo([lat, lon], targetZoom, { duration: 0.9 });
}

// Click on region to zoom and filter
function filtrarPorRegiao(bairro, lat, lon) {
    const selectBairro = document.getElementById('map-filter-bairro');
    if (selectBairro) {
        selectBairro.value = bairro;
    }
    if (lat && lon && map) {
        map.flyTo([lat, lon], 14, { duration: 1.0 });
    }
    loadMapData();
}

// Toggle Heatmap Layer
function toggleHeatmap() {
    if (!heatLayer) return;
    const btn = document.getElementById('btn-toggle-heat');
    if (isHeatmapActive) {
        map.removeLayer(heatLayer);
        isHeatmapActive = false;
        if (btn) btn.className = 'btn btn-outline-glass btn-sm';
        showToast('Mapa de calor de falhas desativado.', 'info');
    } else {
        map.addLayer(heatLayer);
        isHeatmapActive = true;
        if (btn) btn.className = 'btn btn-danger btn-sm';
        showToast('Mapa de calor de falhas ativado.', 'warning');
    }
}

// Initialize Interactive Filter Listeners
function initFilters() {
    const inputs = [
        'map-filter-tipo',
        'map-filter-situacao',
        'map-filter-bairro',
        'map-filter-orgao'
    ];

    inputs.forEach(id => {
        document.getElementById(id)?.addEventListener('change', () => {
            loadMapData();
        });
    });

    const buscaInput = document.getElementById('map-filter-busca');
    if (buscaInput) {
        let debounceTimer;
        buscaInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadMapData();
            }, 350);
        });
    }

    document.getElementById('btn-clear-map-filters')?.addEventListener('click', () => {
        inputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        if (buscaInput) buscaInput.value = '';
        loadMapData();
        map.flyTo(MAP_CENTER, DEFAULT_ZOOM);
    });

    // Populate filter dropdown options dynamically from API
    apiFetch('/api/equipamentos/filtros').then(opts => {
        if (!opts) return;
        const selectBairro = document.getElementById('map-filter-bairro');
        if (selectBairro && opts.bairros) {
            opts.bairros.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b;
                selectBairro.appendChild(opt);
            });
        }
        const selectOrgao = document.getElementById('map-filter-orgao');
        if (selectOrgao && opts.orgaos) {
            opts.orgaos.forEach(o => {
                const opt = document.createElement('option');
                opt.value = o;
                opt.textContent = o;
                selectOrgao.appendChild(opt);
            });
        }
    });

    // Pause/Resume Auto Refresh
    document.getElementById('btn-pause-refresh')?.addEventListener('click', () => {
        isPaused = !isPaused;
        const btn = document.getElementById('btn-pause-refresh');
        if (btn) {
            btn.innerHTML = isPaused ? '<i class="bi bi-play-fill"></i>' : '<i class="bi bi-pause-fill"></i>';
            btn.title = isPaused ? 'Retomar Auto-Refresh' : 'Pausar Auto-Refresh';
        }
    });
}

// Auto Refresh (30s cycle)
function startAutoRefresh() {
    countdownSeconds = autoRefreshInterval;
    setInterval(() => {
        if (!isPaused) {
            countdownSeconds--;
            if (countdownSeconds <= 0) {
                loadDashboardData();
                countdownSeconds = autoRefreshInterval;
            }
            updateRefreshBadge();
        }
    }, 1000);
}

function updateRefreshBadge() {
    const el = document.getElementById('refresh-timer');
    if (el) {
        el.textContent = `${countdownSeconds}s`;
    }
}

function formatarTipo(t) {
    if (!t) return '';
    return t.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatarTipoAgente(t) {
    const mapa = {
        'agente_transito': 'Agente de Trânsito',
        'guarda_municipal': 'Guarda Municipal',
        'policial_militar': 'Policial Militar'
    };
    return mapa[t] || t;
}
