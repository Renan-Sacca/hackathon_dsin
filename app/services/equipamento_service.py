from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.models.historico_equipamento import HistoricoEquipamento
from app.repositories.equipamento_repository import EquipamentoRepository
from app.schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoUpdate,
    HistoricoManutencaoCreate,
)


class EquipamentoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EquipamentoRepository(db)

    def validate_coordinates(self, lat: float, lon: float) -> None:
        """Ensure GPS coordinates are within valid world geographic boundaries."""
        if not (-90.0 <= lat <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Latitude inválida: {lat}. Deve estar entre -90 e 90."
            )
        if not (-180.0 <= lon <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Longitude inválida: {lon}. Deve estar entre -180 e 180."
            )

    def create_equipamento(self, data: EquipamentoCreate) -> Equipamento:
        # Validate duplicate serial number
        existing = self.repo.get_by_numero_serie(data.numero_serie)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipamento com número de série '{data.numero_serie}' já cadastrado."
            )

        self.validate_coordinates(data.latitude, data.longitude)

        # Business rule: mau_funcionamento demands immediate maintenance
        if data.situacao == EquipamentoSituacao.MAU_FUNCIONAMENTO:
            data.manutencao_tipo = ManutencaoTipo.IMEDIATA

        eq = self.repo.create(data)

        # Registra criação no histórico de situações
        self.repo.add_historico(
            equipamento_id=eq.id,
            situacao_anterior=None,
            situacao_nova=eq.situacao,
            motivo=f"Cadastro inicial do equipamento na situação '{eq.situacao.value}'."
        )

        return eq

    def update_equipamento(
        self,
        equipamento_id: int,
        data: EquipamentoUpdate,
        force_reactivation: bool = False
    ) -> Equipamento:
        equipamento = self.repo.get_by_id(equipamento_id)
        if not equipamento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipamento ID {equipamento_id} não encontrado."
            )

        # Check serial number conflict
        if data.numero_serie and data.numero_serie != equipamento.numero_serie:
            existing = self.repo.get_by_numero_serie(data.numero_serie)
            if existing and existing.id != equipamento_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Número de série '{data.numero_serie}' já pertence a outro equipamento."
                )

        # Validate coordinates if provided
        lat = data.latitude if data.latitude is not None else equipamento.latitude
        lon = data.longitude if data.longitude is not None else equipamento.longitude
        self.validate_coordinates(lat, lon)

        situacao_anterior = equipamento.situacao

        # Business Rule 1: Furtado ou Desativado -> Operacional não pode ocorrer diretamente sem validação
        if data.situacao == EquipamentoSituacao.OPERACIONAL and equipamento.situacao in (
            EquipamentoSituacao.FURTADO,
            EquipamentoSituacao.DESATIVADO,
        ):
            if not force_reactivation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Equipamento em situação '{equipamento.situacao.value}' não pode retornar "
                        "diretamente para 'operacional'. É necessária vistoria técnica ou reativação expressa."
                    )
                )

        # Business Rule 2: Mau funcionamento aciona manutenção imediata
        if data.situacao == EquipamentoSituacao.MAU_FUNCIONAMENTO:
            data.manutencao_tipo = ManutencaoTipo.IMEDIATA

        updated_eq = self.repo.update(equipamento, data)

        # Registrar histórico se houve mudança de situação
        if data.situacao and data.situacao != situacao_anterior:
            motivo = f"Alteração de situação de '{situacao_anterior.value}' para '{data.situacao.value}'."
            self.repo.add_historico(
                equipamento_id=updated_eq.id,
                situacao_anterior=situacao_anterior,
                situacao_nova=data.situacao,
                motivo=motivo
            )

        return updated_eq

    def get_equipamento(self, equipamento_id: int) -> Equipamento:
        equipamento = self.repo.get_by_id(equipamento_id)
        if not equipamento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipamento ID {equipamento_id} não encontrado."
            )
        return equipamento

    def get_historico(self, equipamento_id: int) -> List[HistoricoEquipamento]:
        self.get_equipamento(equipamento_id)
        return self.repo.get_historico(equipamento_id)

    def add_historico(self, equipamento_id: int, data: HistoricoManutencaoCreate) -> HistoricoEquipamento:
        equipamento = self.get_equipamento(equipamento_id)
        situacao_anterior = equipamento.situacao

        # Atualiza a situação do equipamento
        equipamento.situacao = data.situacao_nova
        if data.situacao_nova == EquipamentoSituacao.OPERACIONAL:
            equipamento.manutencao_tipo = ManutencaoTipo.NENHUMA

        self.db.commit()

        return self.repo.add_historico(
            equipamento_id=equipamento_id,
            situacao_anterior=situacao_anterior,
            situacao_nova=data.situacao_nova,
            motivo=data.motivo,
            custo_manutencao=data.custo_manutencao,
            tempo_inatividade_horas=data.tempo_inatividade_horas,
            data_mudanca=data.data_mudanca
        )

    def list_equipamentos(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo: Optional[EquipamentoTipo] = None,
        situacao: Optional[EquipamentoSituacao] = None,
        bairro: Optional[str] = None,
        orgao: Optional[str] = None,
        manutencao_tipo: Optional[ManutencaoTipo] = None,
        busca: Optional[str] = None,
        apenas_ativos: bool = True
    ) -> Tuple[List[Equipamento], int]:
        return self.repo.list_equipamentos(
            skip=skip,
            limit=limit,
            tipo=tipo,
            situacao=situacao,
            bairro=bairro,
            orgao=orgao,
            manutencao_tipo=manutencao_tipo,
            busca=busca,
            apenas_ativos=apenas_ativos
        )

    def delete_equipamento(self, equipamento_id: int) -> Equipamento:
        equipamento = self.get_equipamento(equipamento_id)
        return self.repo.soft_delete(equipamento)

    def get_filter_options(self) -> dict:
        return {
            "bairros": self.repo.get_bairros(),
            "orgaos": self.repo.get_orgaos(),
            "tipos": [t.value for t in EquipamentoTipo],
            "situacoes": [s.value for s in EquipamentoSituacao],
            "manutencoes": [m.value for m in ManutencaoTipo],
        }

