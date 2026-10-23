from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.correlacao_service import CorrelacaoService
from app.services.custo_service import CustoService
from app.services.predictive_service import PredictiveService
from app.services.prioridade_instalacao_service import PrioridadeInstalacaoService
from app.services.reforco_service import ReforcoService

router = APIRouter(prefix="/api/preditivo", tags=["Inteligência Preditiva"])


@router.get("/resumo")
def get_resumo_preditivo(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retorna métricas executivas consolidadas da inteligência preditiva."""
    pred_service = PredictiveService(db)
    custo_service = CustoService(db)
    correlacao_service = CorrelacaoService(db)
    prioridade_service = PrioridadeInstalacaoService(db)

    risco = pred_service.calcular_risco_regioes()
    falhas = pred_service.prever_falhas_equipamentos()
    alertas = pred_service.gerar_alertas_preventivos()
    custos = custo_service.projetar_custos_manutencao()
    zonas = correlacao_service.detectar_zonas_correlacao()
    instalacoes = prioridade_service.calcular_prioridade_instalacao()

    bairro_maior_risco = risco[0]["bairro"] if risco else "N/A"
    score_maior_risco = risco[0]["score_geral"] if risco else 0

    return {
        "bairro_maior_risco": bairro_maior_risco,
        "score_maior_risco": score_maior_risco,
        "total_equipamentos_em_risco": len([f for f in falhas if f["probabilidade_falha_percentual"] >= 50]),
        "total_alertas_preventivos": len(alertas),
        "custo_projetado_30d": custos["projecao_30_dias"],
        "zonas_correlacao_detectadas": len(zonas),
        "equipamentos_aguardando_instalacao": len(instalacoes)
    }


@router.get("/risco-regioes")
def get_risco_regioes(dias: int = 180, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna o índice de risco por região e período do dia (manhã, tarde, noite, madrugada)."""
    service = PredictiveService(db)
    return service.calcular_risco_regioes(dias=dias)


@router.get("/equipamentos-risco")
def get_equipamentos_risco(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna os equipamentos com maior probabilidade de falha nos próximos dias e estimativa de MTBF."""
    service = PredictiveService(db)
    return service.prever_falhas_equipamentos()


@router.get("/reforco-agentes")
def get_reforco_agentes(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna as recomendações preditivas de reforço de agentes por região e horário."""
    service = ReforcoService(db)
    return service.estimar_reforco_agentes()


@router.get("/alertas-preventivos")
def get_alertas_preventivos(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna os alertas preventivos gerados por falha iminente, manutenção e anomalias de risco."""
    service = PredictiveService(db)
    return service.gerar_alertas_preventivos()


@router.get("/correlacao-falhas")
def get_correlacao_falhas(dias: int = 180, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna as zonas de suspeita com correlação de falhas simultâneas de infraestrutura."""
    service = CorrelacaoService(db)
    return service.detectar_zonas_correlacao(dias=dias)


@router.get("/custo-projecao")
def get_custo_projecao(dias_historico: int = 180, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retorna a projeção de custo de manutenção esperada para 30, 60 e 90 dias com dados históricos."""
    service = CustoService(db)
    return service.projetar_custos_manutencao(dias_historico=dias_historico)


@router.get("/prioridade-instalacao")
def get_prioridade_instalacao(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna a lista ranqueada de equipamentos aguardando instalação ordenada por score de urgência."""
    service = PrioridadeInstalacaoService(db)
    return service.calcular_prioridade_instalacao()
