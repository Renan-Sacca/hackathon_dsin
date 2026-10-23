# 🌆 PROMETHEUS — F.O.G.O.
**Fiscalização, Operação, Gestão e Ocorrências**

Sistema inteligente de monitoramento urbano para catalogação, operação em tempo real e análise preditiva de equipamentos de segurança e trânsito da cidade.

> 📘 **DOCUMENTAÇÃO VISUAL COMPLETA DISPONÍVEL:**
> * Para ver as **telas com prints reais**, recortes de componentes, diagramas e explicação detalhada de cada endpoint, consulte o: **[Guia Completo do Sistema, Telas & Endpoints (README_GUIA_DO_SISTEMA.md)**.

---

## 🛠 Stack Tecnológica

### Backend

| Tecnologia | Versão | Para que serve |
|-----------|--------|---------------|
| **[FastAPI](https://fastapi.tiangolo.com/)** | 0.115.0 | Framework web Python moderno e rápido. Gera documentação automática (Swagger) em `/docs`. Usa tipagem e async. |
| **[SQLAlchemy](https://www.sqlalchemy.org/)** | 2.0.35 | ORM (Object Relational Mapper) — mapeia classes Python para tabelas do banco de dados. Permite fazer queries sem escrever SQL puro. |
| **[Pydantic](https://docs.pydantic.dev/)** | 2.9.2 | Validação de dados. Define schemas (contratos) para dados de entrada e saída da API. Garante que os dados estão no formato correto. |
| **[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** | 2.5.2 | Carrega variáveis de ambiente do arquivo `.env` para configurações da aplicação. |
| **[python-jose](https://python-jose.readthedocs.io/)** | 3.3.0 | Gera e decodifica tokens JWT (JSON Web Token) para autenticação. |
| **[Passlib](https://passlib.readthedocs.io/) + bcrypt** | 1.7.4 | Faz hash seguro de senhas usando algoritmo bcrypt. Nunca armazena senhas em texto claro. |
| **[Uvicorn](https://www.uvicorn.org/)** | 0.30.6 | Servidor ASGI que roda a aplicação FastAPI. Suporta hot-reload em desenvolvimento. |
| **[SQLite](https://www.sqlite.org/)** | (embutido) | Banco de dados relacional em arquivo. Não precisa de servidor separado. Ideal para hackathon. |

### Frontend

| Tecnologia | Versão | Para que serve |
|-----------|--------|---------------|
| **[Jinja2](https://jinja.palletsprojects.com/)** | 3.1.4 | Motor de templates HTML. Permite usar variáveis Python dentro do HTML. FastAPI renderiza os templates no servidor. |
| **[Bootstrap 5](https://getbootstrap.com/)** | 5.3.3 | Framework CSS para interface responsiva. Fornece componentes prontos (botões, tabelas, modais, etc.). |
| **[Bootstrap Icons](https://icons.getbootstrap.com/)** | 1.11.3 | Biblioteca de ícones SVG do Bootstrap. |
| **[Leaflet.js](https://leafletjs.com/)** | 1.9.x | Biblioteca de mapas interativos. Renderiza equipamentos e agentes geolocalizados em tempo real. |
| **[Chart.js](https://www.chartjs.org/)** | 4.x | Gráficos e visualizações de dados para o dashboard e módulo preditivo. |
| **JavaScript (Fetch API)** | ES6+ | Faz requisições AJAX para a API sem recarregar a página. Manipula a interface dinamicamente. |

### Infraestrutura

| Tecnologia | Para que serve |
|-----------|---------------|
| **[Docker](https://www.docker.com/)** | Empacota a aplicação em um container isolado com todas as dependências. |
| **[Docker Compose](https://docs.docker.com/compose/)** | Orquestra os containers. Define serviços, volumes e redes em um arquivo YAML. |

---

## 🚀 Como Rodar

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **rodando**

### Subir o projeto

```bash
cd "DSIN HACKATON"
docker-compose up --build
```

A aplicação estará disponível em: **http://localhost:8000**

### Parar o projeto

```bash
docker-compose down
```

### Acessar a documentação automática da API

- **Swagger UI**: http://localhost:8000/docs

## 🔑 Credenciais Padrão

| Tipo | Email | Senha |
|------|-------|-------|
| **Administrador** | `admin@prometheus.gov` | `admin123` |
| **Operador** | *(crie pelo painel administrativo)* | — |

O admin padrão é criado automaticamente ao iniciar o sistema pela primeira vez.

---

## 🏗 Arquitetura do Sistema

O projeto segue o padrão de **Arquitetura em Camadas** (Layered Architecture), onde cada camada tem uma responsabilidade específica e só se comunica com a camada adjacente:

```
┌─────────────────────────────────────────────────┐
│                   FRONTEND                       │
│         (Templates Jinja2 + Bootstrap 5)         │
│         (Leaflet.js + Chart.js + Fetch API)      │
└──────────────────────┬──────────────────────────┘
                       │ HTTP Requests
┌──────────────────────▼──────────────────────────┐
│                   ROUTERS                        │
│         (Endpoints da API REST)                  │
│         Recebe requests, retorna responses       │
│         NÃO contém lógica de negócio             │
└──────────────────────┬──────────────────────────┘
                       │ Chama
┌──────────────────────▼──────────────────────────┐
│               DEPENDENCIES                       │
│         (Autenticação / Autorização)             │
│         Extrai e valida JWT token                │
│         Verifica tipo de usuário                 │
└──────────────────────┬──────────────────────────┘
                       │ Injeta user
┌──────────────────────▼──────────────────────────┐
│                  SERVICES                        │
│         (Regras de Negócio)                      │
│         Validação de situação de equipamentos    │
│         Cálculo de métricas e alertas            │
│         Motor de análise preditiva               │
└──────────────────────┬──────────────────────────┘
                       │ Chama
┌──────────────────────▼──────────────────────────┐
│               REPOSITORIES                       │
│         (Acesso ao Banco de Dados)               │
│         Queries SQLAlchemy, CRUD, filtros        │
└──────────────────────┬──────────────────────────┘
                       │ SQL
┌──────────────────────▼──────────────────────────┐
│                  DATABASE                        │
│              (SQLite via SQLAlchemy)              │
└─────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Pastas e Arquivos

```
DSIN HACKATON/
│
├── 📄 Dockerfile                    # Imagem Docker
├── 📄 docker-compose.yml            # Orquestração dos containers
├── 📄 requirements.txt              # Dependências Python
├── 📄 .env                          # Variáveis de ambiente
├── 📄 .dockerignore                 # Arquivos ignorados pelo Docker
├── 📄 README.md                     # Este arquivo principal
├── 📄 README_GUIA_DO_SISTEMA.md     # 📘 Manual completo com prints e endpoints
├── 📄 mapa_funcionalidades_testes.md # 🗺️ Rastreabilidade edital e roteiro de testes
├── 📄 TASKS.md                      # Lista de tarefas do projeto
├── 📄 seed_demo.py                  # Script de dados de demonstração (50+ eq, 20+ ag)
├── 📄 seed_historico.py             # Script de histórico sintético calibrado (Parte 3)
│
├── 📁 docs/                         # Documentação visual
│   └── 📁 screenshots/              # 35+ capturas reais de telas e recortes
│
├── 📁 tests/                        # Suíte de Testes Automatizados (unittest)
│   ├── 📄 test_historico.py         # Testes de histórico, custos e transições
│   └── 📄 test_predictive.py        # 8 testes cobrindo MTBF, XAI, risco e custos
│
├── 📁 app/                          # ← CÓDIGO DA APLICAÇÃO
   ├── 📄 __init__.py               # Marca 'app' como pacote Python
   ├── 📄 main.py                   # Ponto de entrada do FastAPI
   │
   ├── 📁 core/                     # Configurações centrais
   │   ├── 📄 config.py             # Settings do .env (pydantic-settings)
   │   └── 📄 security.py           # JWT + bcrypt (hash/verify/token)
   │
   ├── 📁 database/                 # Camada de banco de dados
   │   ├── 📄 base.py               # Base declarativa do SQLAlchemy
   │   ├── 📄 connection.py         # Engine, SessionLocal, get_db()
   │   └── 📄 seed.py               # Dados iniciais (admin padrão)
   │
   ├── 📁 models/                   # Modelos SQLAlchemy (tabelas)
   │   ├── 📄 __init__.py           # Exporta todos os modelos
   │   ├── 📄 user.py               # User (id, nome, email, senha, tipo)
   │   ├── 📄 equipamento.py        # Equipamento (tipo, situação, localização, etc.)
   │   ├── 📄 equipamento_propriedade.py # Propriedades extras dinâmicas (JSON)
   │   ├── 📄 agente.py             # Agente (matrícula, tipo, órgão, situação)
   │   ├── 📄 historico_equipamento.py  # Histórico de intervenções e custos (Parte 1 e 3)
   │   └── 📄 ocorrencia.py         # Ocorrências geoespaciais por turno (Parte 3)
   │
   ├── 📁 schemas/                  # Schemas Pydantic (validação e contratos)
   │   ├── 📄 __init__.py
   │   ├── 📄 user.py               # UserCreate, UserLogin, TokenResponse
   │   ├── 📄 equipamento.py        # EquipamentoCreate, EquipamentoUpdate, Response
   │   └── 📄 agente.py             # AgenteCreate, AgenteUpdate, AgenteResponse
   │
   ├── 📁 repositories/             # Acesso ao banco (queries SQLAlchemy)
   │   ├── 📄 user_repository.py    # CRUD de User
   │   ├── 📄 equipamento_repository.py # CRUD + filtros de Equipamento
   │   ├── 📄 agente_repository.py  # CRUD + filtros de Agente
   │   ├── 📄 dashboard_repository.py   # Queries agregadas para métricas
   │   └── 📄 predictive_repository.py  # Queries históricas para preditivo (Parte 3)
   │
   ├── 📁 services/                 # Regras de Negócio & Algoritmos
   │   ├── 📄 auth_service.py       # Registro e login
   │   ├── 📄 equipamento_service.py # Validação, transição de situação e gatilhos
   │   ├── 📄 agente_service.py     # Validação de matrícula, situação e escalas
   │   ├── 📄 dashboard_service.py  # Cálculo de métricas e alertas em tempo real
   │   ├── 📄 predictive_service.py # Motor de análise preditiva (Risco, MTBF, XAI)
   │   ├── 📄 correlacao_service.py # Detecção de falhas correlacionadas em infraestrutura
   │   ├── 📄 custo_service.py      # Projeção orçamentária para 30, 60 e 90 dias
   │   ├── 📄 reforco_service.py    # Dimensionamento proativo de equipes de campo
   │   └── 📄 prioridade_instalacao_service.py # Score e fila de implantação
   │
   ├── 📁 routers/                  # Endpoints da API REST
   │   ├── 📄 auth.py               # POST /api/auth/login, /register, /logout
   │   ├── 📄 equipamentos.py       # CRUD /api/equipamentos e /historico
   │   ├── 📄 agentes.py            # CRUD /api/agentes
   │   ├── 📄 dashboard.py          # GET /api/dashboard/metricas, /mapa, /alertas, /regioes
   │   ├── 📄 predictive.py         # GET /api/preditivo/* (Risco, MTBF, Reforço, Custos)
   │   └── 📄 pages.py              # Rotas HTML (login, dashboard, cadastros, preditivo)
   │
   ├── 📁 dependencies/             # Injeção de dependências
   │   └── 📄 auth.py               # get_current_user, require_admin
   │
   ├── 📁 templates/                # HTML (Jinja2 + Bootstrap 5 + Glassmorphism)
   │   ├── 📄 base.html             # Layout base (navbar, sino de alertas, footer)
   │   ├── 📄 login.html            # Tela de login com preenchimento facilitado
   │   └── 📁 admin/                # Páginas do administrador/operador
   │       ├── 📄 dashboard.html    # Central de Operações (mapa + KPIs + alertas)
   │       ├── 📄 preditivo.html    # Cidade Preditiva (mapa de risco, gráficos, fila)
   │       ├── 📁 equipamentos/
   │       │   ├── 📄 lista.html    # Listagem com modais de detalhes e histórico
   │       │   └── 📄 form.html     # Cadastro/edição com campos adaptativos
   │       └── 📁 agentes/
   │           ├── 📄 lista.html    # Listagem de agentes com filtros
   │           └── 📄 form.html     # Cadastro/edição de agente
   │
   └── 📁 static/                   # Arquivos estáticos
       ├── 📁 css/
       │   └── 📄 style.css         # Design system (Cyber dark theme, glassmorphism)
       └── 📁 js/
           ├── 📄 app.js            # Lógica global (fetch, toasts, loaders)
           ├── 📄 dashboard.js      # Mapa Leaflet, KPIs, auto-refresh (30s)
           └── 📄 preditivo.js      # Gráficos Chart.js, mapa de risco e modal XAI
```

---

## 📂 Estrutura dos Models

### `app/models/user.py` — Tabela `users`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador único |
| `nome` | String | Nome completo |
| `email` | String (unique) | Email de login |
| `senha_hash` | String | Hash bcrypt da senha |
| `tipo` | Enum (ADMIN/OPERADOR) | Tipo de usuário para RBAC |
| `ativo` | Boolean | Soft delete (True = ativo) |
| `criado_em` | DateTime | Auto-preenchido na criação |
| `atualizado_em` | DateTime | Auto-preenchido na atualização |

### `app/models/equipamento.py` — Tabela `equipamentos`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador único |
| `numero_serie` | String (unique) | Número de série do equipamento |
| `marca` | String | Fabricante |
| `modelo` | String | Modelo do equipamento |
| `tipo` | Enum | radar_velocidade, camera_monitoramento, balanca_caminhao, etc. |
| `situacao` | Enum | nao_instalado, operacional, mau_funcionamento, manutencao, desativado, furtado |
| `manutencao_tipo` | Enum | nenhuma, imediata, agendada |
| `proxima_manutencao` | Date (nullable) | Data da próxima manutenção agendada |
| `localizacao_cep` | String | CEP da instalação |
| `localizacao_bairro` | String | Bairro |
| `localizacao_cidade` | String | Cidade |
| `localizacao_uf` | String | UF (ex: SP, RJ) |
| `localizacao_rua` | String | Nome da rua/avenida |
| `localizacao_referencia` | String | Referência (ex: "oposto ao nº 181", "KM 203") |
| `latitude` | Float | Coordenada GPS latitude |
| `longitude` | Float | Coordenada GPS longitude |
| `orgao_responsavel` | String | Órgão responsável pelo equipamento |
| `ativo` | Boolean | Soft delete |
| `criado_em` | DateTime | Auto-preenchido na criação |
| `atualizado_em` | DateTime | Auto-preenchido na atualização |

### `app/models/equipamento_propriedade.py` — Tabela `equipamento_propriedades`

Armazena propriedades específicas por tipo de equipamento em formato chave-valor:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `equipamento_id` | FK → equipamentos | Equipamento dono da propriedade |
| `chave` | String | Nome da propriedade (ex: `visao_noturna`, `resolucao`, `velocidade_maxima`) |
| `valor` | String | Valor da propriedade |

**Exemplos de uso:**
- Câmera: `visao_noturna=true`, `resolucao=4K`, `colorida=true`
- Radar de velocidade: `velocidade_maxima=80`, `faixa=dupla`
- Radar de semáforo: `direcoes_fiscalizadas=norte,sul`

### `app/models/agente.py` — Tabela `agentes`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `nome` | String | Nome completo |
| `matricula` | String (unique) | Matrícula funcional |
| `tipo` | Enum | agente_transito / guarda_municipal / policial_militar |
| `orgao` | String | Órgão de vínculo |
| `telefone` | String | Contato |
| `situacao` | Enum | em_atividade / fora_de_servico / ferias / afastado |
| `latitude` | Float (nullable) | Posição atual |
| `longitude` | Float (nullable) | Posição atual |
| `criado_em` | DateTime | Auto-preenchido |
| `atualizado_em` | DateTime | Auto-preenchido |

### `app/models/historico_equipamento.py` — Tabela `historico_equipamentos` (Partes 1 e 3)

Registra o histórico de ciclo de vida, transições de estado, custos e horas de inatividade (*downtime*):

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `equipamento_id` | FK → equipamentos | Equipamento relacionado |
| `situacao_anterior` | Enum (nullable) | Situação antes da mudança |
| `situacao_nova` | Enum | Nova situação cadastrada |
| `data_mudanca` | DateTime | Carimbo de data/hora do evento |
| `motivo` | String | Justificativa ou descrição do serviço |
| `custo_manutencao` | Float | Custo financeiro da intervenção em R$ |
| `tempo_inatividade_horas` | Float | Horas de indisponibilidade operacional (*downtime*) |

### `app/models/ocorrencia.py` — Tabela `ocorrencias` (Parte 3)

Base geoespacial e temporal de eventos urbanos que alimenta os modelos de risco e correlação preditiva:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `tipo` | Enum | acidente_transito, lentidao_congestionamento, furto_roubo, vandalismo, falha_semaforo, etc. |
| `severidade` | Enum | baixa, media, alta, critica |
| `data_hora` | DateTime | Timestamp do registro |
| `bairro` | String | Bairro da ocorrência |
| `latitude` | Float | Coordenada GPS latitude |
| `longitude` | Float | Coordenada GPS longitude |
| `equipamento_relacionado_id`| FK (nullable) | Equipamento próximo afetado |
| `agente_responsavel_id` | FK (nullable) | Equipe destacada para atendimento |

---

## 🔄 Fluxo de Situação de Equipamento

```
Cadastro
   │
   ▼
[não instalado]
   │
   ▼
[operacional] ◄──────────────────────┐
   │                                 │
   ├──► [mau funcionamento]          │
   │         │                       │
   │         ▼                       │
   │    [manutenção imediata]        │
   │         │                       │
   │         └────────────────────── ┘ (após manutenção)
   │
   ├──► [manutenção agendada]
   │         │
   │         └────────────────────── ┘ (após manutenção)
   │
   ├──► [desativado]
   │
   └──► [furtado]
```

---

## ⚙ Regras de Negócio

### 1. Transição de Situação de Equipamento
- Equipamentos `furtado` ou `desativado` **não podem** voltar a `operacional` diretamente — requerem validação e confirmação manual expressa
- Mau funcionamento automaticamente aciona necessidade de manutenção `imediata`
- Equipamentos com `proxima_manutencao` nos próximos 3 dias geram alerta `ATENÇÃO`

### 2. Alertas Automáticos por Criticidade
- **CRÍTICO**: equipamento em `mau_funcionamento` ou `furtado`
- **URGENTE**: manutenção de tipo `imediata` pendente
- **ATENÇÃO**: manutenção agendada para os próximos 3 dias

### 3. Modelos da Cidade Preditiva (Parte 3)
- **MTBF & Previsão de Falhas:** Cálculo de tempo médio entre falhas baseado em histórico de 6 meses; probabilidade percentual de nova quebra e data estimada.
- **Explainable AI (XAI):** Transparência total demonstrando as variáveis estatísticas utilizadas e indicando ações preventivas para os gestores.
- **Reforço Proativo de Equipes:** Alocação de agentes cruzando risco regional por período com o efetivo em campo e determinando especialidade necessária (Trânsito vs Guarda).
- **Zonas de Correlação:** Agrupamento geoespacial de falhas simultâneas em raio de 300m para diagnosticar causas de infraestrutura compartilhada (queda de energia, fibra cortada).
- **Projeção Orçamentária:** Estimativa de custos de manutenção para 30, 60 e 90 dias com comparação visual em gráfico Chart.js.
- **Fila Ranqueada de Instalação:** Priorização matemática ponderando 60% de risco do bairro de destino + 40% de tempo de espera.

### 4. Propriedades Dinâmicas por Tipo
- Cada tipo de equipamento possui um conjunto específico de propriedades adicionais injetadas dinamicamente
- Armazenadas em tabela chave-valor para máxima flexibilidade sem migrações adicionais

### 5. Soft Delete
- Equipamentos e agentes **nunca são deletados** fisicamente do banco
- São **desativados** (campo `ativo = False`), preservando integridade referencial e auditoria

### 6. Permissões (RBAC) & Segurança
- **Admin**: acesso total — cadastros, edições, exclusões, histórico e calibração de modelos
- **Operador**: acesso ao dashboard, consulta de ativos e visualização de alertas, sem privilégios de exclusão
- **Proteção contra SQL Injection**: 100% das consultas utilizam SQLAlchemy ORM com parametrização automática
- **Sanitização XSS**: camada de sanitização automática em todos os Schemas Pydantic
- **JWT**: autenticação stateless com tokens de expiração configurável

---

## 🧪 Suíte de Testes Automatizados (43 Testes)

O PROMETHEUS conta com uma suíte abrangente de **43 testes automatizados** baseada em `unittest` e asserções HTTP, cobrindo autenticação, regras de negócio de equipamentos e viaturas, integridade do dashboard em tempo real, integração de endpoints e todos os algoritmos preditivos:

```powershell
docker exec prometheus-app python -m unittest discover tests
```

Resultado verificado:
```text
...........................................
----------------------------------------------------------------------
Ran 43 tests in 5.116s

OK
```

### Cobertura da Suíte de Testes:

| Arquivo de Teste | Qtd. Testes | Escopo & Regras Validadas |
| :--- | :---: | :--- |
| **`tests/test_auth.py`** | **6** | Registro de operadores, hash bcrypt de senhas, validação de e-mails duplicados, login e emissão de tokens JWT, validação de payload/claims e bloqueio de usuários inativos. |
| **`tests/test_equipamentos.py`** | **6** | Cadastro de ativos urbanos, unicidade de número de série, validação geográfica de coordenadas GPS (-90..90, -180..180), regra automática `MAU_FUNCIONAMENTO -> MANUTENCAO_IMEDIATA`, filtros múltiplos e soft delete. |
| **`tests/test_agentes.py`** | **6** | Cadastro de agentes (Trânsito, Guarda Municipal, PM), validação de matrícula única, coordenadas GPS, atualização de turno/situação operacional, busca textual e soft delete. |
| **`tests/test_dashboard.py`** | **4** | Agregação de KPIs executivos ao vivo, integridade dos marcadores geolocalizados de mapa para Leaflet, ordenação de alertas críticos ativos e cálculo da taxa de saúde operacional por bairro. |
| **`tests/test_historico_manutencao.py`** | **3** | Consulta do histórico de intervenções, cálculo de tempo de inatividade (*downtime*), acúmulo financeiro de custos e auto-registro histórico em transições de situação. |
| **`tests/test_preditivo.py`** | **8** | Modelos preditivos da Parte 3: matriz de risco regional por turno, MTBF e probabilidade de quebra, alertas preventivos por limiar crítico, explicabilidade da IA (XAI), zonas de falhas correlacionadas (raio 300m), projeção de custos (30/60/90 dias) e fila ponderada de instalação. |
| **`tests/test_api_endpoints.py`** | **10** | Testes de integração HTTP contra o servidor ativo: Swagger/OpenAPI, ciclo de autenticação JWT Bearer, acesso a rotas protegidas (`/api/auth/me`), contratos do dashboard, listagem paginada de equipamentos e viaturas, e endpoints da Cidade Preditiva. |

---

## 📮 Postman Collection Automatizada

Para testes funcionais de integração e demonstração dinâmica da API RESTful, o projeto disponibiliza uma coleção completa no padrão **Postman Collection v2.1.0**:

📁 **Arquivo:** [`PROMETHEUS_API.postman_collection.json`](file:///c:/Users/renan/OneDrive/Desktop/DSIN%20HACKATON/PROMETHEUS_API.postman_collection.json)

### Destaques e Automações da Coleção:
1. **Captura Dinâmica de JWT no Login:**
   - Ao executar a requisição `1. Autenticação & Sessão > Login`, um script de teste captura automaticamente o `access_token` retornado e atualiza a variável global `{{token}}`.
   - Todas as requisições protegidas herdam autenticação `Bearer {{token}}` automaticamente.
2. **Encadeamento Automático de IDs:**
   - Criar um equipamento ou agente salva o ID gerado nas variáveis `{{createdEquipamentoId}}` e `{{createdAgenteId}}`, alimentando as requisições de consulta, edição, histórico e exclusão sem intervenção manual.
3. **Asserções Automatizadas em Cada Endpoint:**
   - Valida status HTTP (`200 OK`, `201 Created`), tempo de resposta (< 2000ms) e integridade dos schemas retornados.
4. **Compatibilidade Total:**
   - Pode ser importado diretamente no **Postman**, **Insomnia**, **Bruno**, extensão **Thunder Client (VS Code)** ou executado em pipeline CI/CD via **Newman CLI**:
     ```powershell
     npx newman run PROMETHEUS_API.postman_collection.json
     ```

---

## 🛠 Ferramentas de Demonstração

### Seed de Dados (`seed_demo.py`)
Script para popular o banco com dados realistas para demonstração:
- 50+ equipamentos de tipos variados distribuídos pela cidade
- 20+ agentes de diferentes tipos e situações
- Equipamentos em diversas situações (operacional, mau funcionamento, furtado, etc.)

```bash
docker exec prometheus-app python seed_demo.py
```

### Seed de Histórico (`seed_historico.py`) — Parte 3
Script para gerar 6+ meses de histórico sintético para alimentar o motor preditivo:

```bash
docker exec prometheus-app python seed_historico.py
```

---

## 📌 Observações

- **Escalabilidade**: A arquitetura em camadas permite substituir o SQLite por PostgreSQL sem alterar a lógica de negócio — basta mudar a `DATABASE_URL` no `.env`.
- **Mapa**: Utiliza Leaflet.js com tiles gratuitos do OpenStreetMap — sem custo de API key.
- **Parte 3 (Preditivo)**: Utiliza análise estatística sobre dados históricos gerados pelo `seed_historico.py`. A tecnologia é simples e explicável por design, conforme os critérios do hackathon.
