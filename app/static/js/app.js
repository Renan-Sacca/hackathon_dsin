/**
 * PROMETHEUS — F.O.G.O. Core Client Application Script
 * Provides global HTTP fetch client, toast notifications, dynamic fields, and auth helpers.
 */

// Toast Notification System
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-item border-${type}`;

    let icon = 'bi-info-circle-fill text-info';
    if (type === 'success') icon = 'bi-check-circle-fill text-success';
    if (type === 'danger' || type === 'error') icon = 'bi-exclamation-triangle-fill text-danger';
    if (type === 'warning') icon = 'bi-exclamation-circle-fill text-warning';

    toast.innerHTML = `
        <i class="bi ${icon} fs-5"></i>
        <div class="flex-grow-1 text-sm">${message}</div>
        <button type="button" class="btn-close btn-close-white ms-auto" aria-label="Close"></button>
    `;

    toast.querySelector('.btn-close').addEventListener('click', () => {
        toast.remove();
    });

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }
    }, 4500);
}

// Token helper
function getToken() {
    const local = localStorage.getItem('access_token');
    if (local) return local;

    // Check cookie
    const match = document.cookie.match(new RegExp('(^| )access_token=([^;]+)'));
    if (match) {
        const val = decodeURIComponent(match[2]);
        return val.startsWith('Bearer ') ? val.substring(7) : val;
    }
    return null;
}

function setToken(token) {
    localStorage.setItem('access_token', token);
    document.cookie = `access_token=Bearer ${token}; path=/; max-age=86400; SameSite=Lax`;
}

function removeToken() {
    localStorage.removeItem('access_token');
    document.cookie = 'access_token=; path=/; max-age=0; SameSite=Lax';
}

// Authenticated API Fetch
async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = options.headers || {};

    if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    options.headers = headers;

    try {
        const response = await fetch(url, options);

        if (response.status === 401) {
            // Not authenticated, redirect to login
            if (!window.location.pathname.includes('/login')) {
                removeToken();
                window.location.href = '/login?expired=1';
                return null;
            }
        }

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const errorMsg = data?.detail || `Erro ${response.status}: Falha na operação.`;
            showToast(errorMsg, 'danger');
            throw new Error(errorMsg);
        }

        return data;
    } catch (err) {
        if (!options.silentError) {
            console.error('Fetch error:', err);
        }
        throw err;
    }
}

// Global Logout
async function logoutUser() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
        // Ignore network errors on logout
    }
    removeToken();
    window.location.href = '/login';
}

// Dynamic properties definition by Equipamento Tipo (P1-JS-02)
const TIPO_PROPRIEDADES_CONFIG = {
    'radar_velocidade': [
        { chave: 'velocidade_maxima', label: 'Velocidade Máxima (km/h)', placeholder: 'Ex: 60', type: 'number' },
        { chave: 'qtd_faixas', label: 'Qtd. de Faixas Fiscalizadas', placeholder: 'Ex: 2', type: 'number' },
        { chave: 'sentido', label: 'Sentido Fiscalizado', placeholder: 'Ex: Bairro-Centro' }
    ],
    'radar_semaforo': [
        { chave: 'direcoes_fiscalizadas', label: 'Direções Fiscalizadas', placeholder: 'Ex: Norte/Sul, Leste/Oeste' },
        { chave: 'tempo_amarelo_segundos', label: 'Tempo do Sinal Amarelo (segundos)', placeholder: 'Ex: 4', type: 'number' },
        { chave: 'tipo_cruzamento', label: 'Tipo de Cruzamento', placeholder: 'Ex: Binário / Semaforizado 4 tempos' }
    ],
    'radar_conversao': [
        { chave: 'manobra_fiscalizada', label: 'Manobra Proibida Fiscalizada', placeholder: 'Ex: Conversão à esquerda proibida' },
        { chave: 'horario_restricao', label: 'Horário de Restrição', placeholder: 'Ex: 06h às 20h' }
    ],
    'camera_monitoramento': [
        { chave: 'resolucao', label: 'Resolução de Captura', placeholder: 'Ex: 4K UHD, Full HD 1080p' },
        { chave: 'visao_noturna', label: 'Visão Noturna / Infravermelho', placeholder: 'Sim / Não' },
        { chave: 'ptz_360', label: 'Controle PTZ (Giro 360°)', placeholder: 'Sim / Não' },
        { chave: 'zoom_optico', label: 'Zoom Óptico', placeholder: 'Ex: 30x' }
    ],
    'balanca_caminhao': [
        { chave: 'capacidade_maxima_ton', label: 'Capacidade Máxima (Toneladas)', placeholder: 'Ex: 80', type: 'number' },
        { chave: 'tipo_sensores', label: 'Tipo de Sensores de Carga', placeholder: 'Ex: Células piezoelétricas' }
    ],
    'veiculo_fiscalizacao_estacionamento': [
        { chave: 'placa_veiculo', label: 'Placa do Veículo Fiscalizador', placeholder: 'Ex: BRA2E19' },
        { chave: 'qtd_cameras_ocr', label: 'Câmeras OCR Embarcadas', placeholder: 'Ex: 4', type: 'number' }
    ],
    'cancela_automatizada': [
        { chave: 'tempo_abertura_seg', label: 'Tempo de Abertura (s)', placeholder: 'Ex: 1.5', type: 'number' },
        { chave: 'leitor_rfid', label: 'Leitor RFID / ConectCar / SemParar', placeholder: 'Sim / Não' }
    ],
    'veiculo_transporte': [
        { chave: 'modalidade', label: 'Modalidade', placeholder: 'Ex: Táxi, Escolar, Transporte App' },
        { chave: 'placa', label: 'Placa do Veículo', placeholder: 'Ex: BRA9X88' },
        { chave: 'capacidade_passageiros', label: 'Capacidade de Passageiros', placeholder: 'Ex: 16', type: 'number' }
    ],
    'totem_estacionamento': [
        { chave: 'pagamento_pix_cartao', label: 'Meios de Pagamento', placeholder: 'Ex: PIX, Débito, Crédito, Moedas' },
        { chave: 'conexao', label: 'Tipo de Conexão', placeholder: 'Ex: 4G LTE, Fibra' }
    ],
    'patinete_eletrico': [
        { chave: 'autonomia_km', label: 'Autonomia da Bateria (km)', placeholder: 'Ex: 35', type: 'number' },
        { chave: 'bloqueio_remoto', label: 'Bloqueio Remoto Ativo', placeholder: 'Sim / Não' }
    ],
    'moto_agente': [
        { chave: 'placa', label: 'Placa da Motocicleta', placeholder: 'Ex: PRM1A23' },
        { chave: 'prefixo', label: 'Prefixo Operacional', placeholder: 'Ex: MT-04' }
    ],
    'viatura_guarda': [
        { chave: 'prefixo', label: 'Prefixo da Viatura', placeholder: 'Ex: GCM-12' },
        { chave: 'blindagem', label: 'Nível de Blindagem', placeholder: 'Ex: Leve / Padrão' }
    ],
    'viatura_policia': [
        { chave: 'prefixo', label: 'Prefixo Policial', placeholder: 'Ex: PM-2041' },
        { chave: 'camera_embarcada', label: 'Câmera Embarcada Integrada', placeholder: 'Sim / Não' }
    ]
};

// Render Dynamic Properties for Equipamento Form
function renderDynamicProperties(tipo, existingProps = []) {
    const container = document.getElementById('dynamic-properties-container');
    if (!container) return;

    container.innerHTML = '';
    const config = TIPO_PROPRIEDADES_CONFIG[tipo] || [];
    const propsMap = {};
    existingProps.forEach(p => { propsMap[p.chave] = p.valor; });

    if (config.length === 0) {
        container.innerHTML = `
            <div class="p-3 text-muted text-center border border-dashed rounded">
                <i class="bi bi-info-circle me-1"></i>
                Nenhuma propriedade pré-configurada para este tipo. Utilize o botão abaixo para adicionar propriedades personalizadas.
            </div>
        `;
    }

    config.forEach(field => {
        const valor = propsMap[field.chave] !== undefined ? propsMap[field.chave] : '';
        const col = document.createElement('div');
        col.className = 'col-md-6 mb-3 property-row';
        col.innerHTML = `
            <label class="form-label">${field.label}</label>
            <div class="input-group">
                <input type="hidden" name="prop_chave[]" value="${field.chave}">
                <input type="${field.type || 'text'}" 
                       name="prop_valor[]" 
                       class="form-control" 
                       placeholder="${field.placeholder || ''}" 
                       value="${valor}">
            </div>
        `;
        container.appendChild(col);
    });

    // Render custom properties that aren't in predefined config
    existingProps.forEach(p => {
        const isPredefined = config.some(f => f.chave === p.chave);
        if (!isPredefined) {
            addCustomPropertyRow(p.chave, p.valor);
        }
    });
}

function addCustomPropertyRow(chave = '', valor = '') {
    const container = document.getElementById('dynamic-properties-container');
    if (!container) return;

    const row = document.createElement('div');
    row.className = 'col-12 mb-2 property-row custom-prop-row';
    row.innerHTML = `
        <div class="input-group">
            <input type="text" name="prop_chave[]" class="form-control" placeholder="Chave da propriedade" value="${chave}" required>
            <input type="text" name="prop_valor[]" class="form-control" placeholder="Valor da propriedade" value="${valor}" required>
            <button type="button" class="btn btn-outline-danger" onclick="this.closest('.property-row').remove()">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(row);
}

// Gather properties array from form
function collectPropertiesFromForm() {
    const rows = document.querySelectorAll('.property-row');
    const propriedades = [];
    rows.forEach(r => {
        const chaveInput = r.querySelector('input[name="prop_chave[]"]');
        const valorInput = r.querySelector('input[name="prop_valor[]"]');
        if (chaveInput && valorInput) {
            const chave = chaveInput.value.trim();
            const valor = valorInput.value.trim();
            if (chave && valor) {
                propriedades.push({ chave, valor });
            }
        }
    });
    return propriedades;
}
