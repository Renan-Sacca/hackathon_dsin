from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(include_in_schema=False)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Renderiza a página de login."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"hide_navbar": True}
    )


@router.get("/", response_class=RedirectResponse)
def index_redirect():
    """Redireciona a raiz para a Central de Operações."""
    return RedirectResponse(url="/admin/dashboard")


@router.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    """Renderiza a Central de Operações com Mapa Interativo e KPIs em tempo real."""
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={"active_page": "dashboard"}
    )


@router.get("/admin/equipamentos", response_class=HTMLResponse)
def equipamentos_lista_page(request: Request):
    """Renderiza a listagem de equipamentos."""
    return templates.TemplateResponse(
        request=request,
        name="admin/equipamentos/lista.html",
        context={"active_page": "equipamentos"}
    )


@router.get("/admin/equipamentos/novo", response_class=HTMLResponse)
def equipamentos_novo_page(request: Request):
    """Renderiza o formulário de cadastro de equipamento."""
    return templates.TemplateResponse(
        request=request,
        name="admin/equipamentos/form.html",
        context={"active_page": "equipamentos", "is_edit": False, "equipamento_id": None}
    )


@router.get("/admin/equipamentos/{equipamento_id}/editar", response_class=HTMLResponse)
def equipamentos_editar_page(request: Request, equipamento_id: int):
    """Renderiza o formulário de edição de equipamento."""
    return templates.TemplateResponse(
        request=request,
        name="admin/equipamentos/form.html",
        context={
            "active_page": "equipamentos",
            "is_edit": True,
            "equipamento_id": equipamento_id
        }
    )


@router.get("/admin/agentes", response_class=HTMLResponse)
def agentes_lista_page(request: Request):
    """Renderiza a listagem de agentes."""
    return templates.TemplateResponse(
        request=request,
        name="admin/agentes/lista.html",
        context={"active_page": "agentes"}
    )


@router.get("/admin/agentes/novo", response_class=HTMLResponse)
def agentes_novo_page(request: Request):
    """Renderiza o formulário de cadastro de agente."""
    return templates.TemplateResponse(
        request=request,
        name="admin/agentes/form.html",
        context={"active_page": "agentes", "is_edit": False, "agente_id": None}
    )


@router.get("/admin/agentes/{agente_id}/editar", response_class=HTMLResponse)
def agentes_editar_page(request: Request, agente_id: int):
    """Renderiza o formulário de edição de agente."""
    return templates.TemplateResponse(
        request=request,
        name="admin/agentes/form.html",
        context={
            "active_page": "agentes",
            "is_edit": True,
            "agente_id": agente_id
        }
    )


@router.get("/admin/preditivo", response_class=HTMLResponse)
def preditivo_page(request: Request):
    """Renderiza a Visão Preditiva com análise temporal, projeção de custos, correlação de falhas e reforço operacional."""
    return templates.TemplateResponse(
        request=request,
        name="admin/preditivo.html",
        context={"active_page": "preditivo"}
    )

