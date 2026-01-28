"""
Modelos Pydantic para validação e serialização dos registros Cielo EDI.

Cada modelo representa um tipo de registro conforme especificação v15.14.1.
"""

from datetime import date, time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from cielo_edi.dominios import (
    CANAL_VENDA,
    CODIGOS_BANDEIRAS,
    FORMA_PAGAMENTO,
    GRUPO_CARTOES,
    MOTIVOS_AJUSTE,
    STATUS_PAGAMENTO,
    TIPO_CAPTURA,
    TIPO_CARTAO,
    TIPO_LIQUIDACAO,
    TIPO_PRECIFICACAO,
    TIPOS_ARQUIVO,
    TIPOS_LANCAMENTO,
)


class BaseRegistro(BaseModel):
    """Modelo base para todos os registros EDI"""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    tipo_registro: str = Field(..., description="Tipo do registro (0, D, E, 8, A, B, C, R, 9)")

    @field_serializer('*', when_used='json')
    def serialize_decimal_as_float(self, value: Any) -> Any:
        """Serializa campos Decimal como float no JSON"""
        if isinstance(value, Decimal):
            return float(value)
        return value


class RegistroHeader(BaseRegistro):
    """Registro 0 - Header do arquivo EDI"""

    tipo_registro: str = Field(default="0", frozen=True)
    estabelecimento_matriz: str = Field(..., max_length=10, description="Número do EC matriz")
    data_processamento: Optional[date] = Field(None, description="Data de processamento")
    periodo_inicial: Optional[date] = Field(None, description="Período inicial do extrato")
    periodo_final: Optional[date] = Field(None, description="Período final do extrato")
    sequencia: str = Field(..., max_length=7, description="Número sequencial do arquivo")
    empresa_adquirente: str = Field(default="CIELO", max_length=5)
    opcao_extrato: str = Field(..., max_length=2, description="Tipo do arquivo (03, 04, 09, 15, 16)")
    transmissao: str = Field(..., max_length=1)
    caixa_postal: str = Field(default="", max_length=20)
    versao_layout: str = Field(..., max_length=3, description="Versão do layout")

    @property
    def opcao_extrato_descricao(self) -> str:
        """Descrição do tipo de arquivo"""
        return TIPOS_ARQUIVO.get(self.opcao_extrato, "Desconhecido")


class RegistroURAgenda(BaseRegistro):
    """Registro D - Unidade de Recebimento (UR) Agenda"""

    tipo_registro: str = Field(default="D", frozen=True)
    estabelecimento_submissor: str = Field(..., max_length=10)
    cpf_cnpj_titular: str = Field(..., max_length=14)
    cpf_cnpj_titular_movimento: str = Field(..., max_length=14)
    cpf_cnpj_recebedor: str = Field(..., max_length=14)
    bandeira: str = Field(..., max_length=3)
    tipo_liquidacao: str = Field(..., max_length=3)
    matriz_pagamento: str = Field(..., max_length=10)
    status_pagamento: str = Field(..., max_length=2)
    sinal_valor_bruto: str = Field(..., max_length=1)
    valor_bruto: Decimal = Field(..., decimal_places=2, description="Valor bruto em reais")
    valor_bruto_original: str = Field(..., max_length=13, description="Valor bruto original do arquivo EDI")
    sinal_taxa_administrativa: str = Field(..., max_length=1)
    valor_taxa_administrativa: Decimal = Field(..., decimal_places=2)
    valor_taxa_administrativa_original: str = Field(..., max_length=13, description="Valor taxa original do arquivo EDI")
    sinal_valor_liquido: str = Field(..., max_length=1)
    valor_liquido: Decimal = Field(..., decimal_places=2, description="Valor líquido em reais")
    valor_liquido_original: str = Field(..., max_length=13, description="Valor líquido original do arquivo EDI")
    banco: str = Field(..., max_length=4)
    agencia: str = Field(..., max_length=5)
    conta: str = Field(..., max_length=20)
    digito_conta: str = Field(..., max_length=1)
    quantidade_lancamentos: int = Field(..., ge=0)
    tipo_lancamento: str = Field(..., max_length=2)
    chave_ur: str = Field(..., max_length=100)
    data_pagamento: Optional[date] = None
    data_envio_banco: Optional[date] = None
    data_vencimento_original: Optional[date] = None
    numero_estabelecimento_pagamento: str = Field(default="", max_length=10)
    indicativo_lancamento_pendente: str = Field(default="", max_length=1)
    indicativo_reenvio_pagamento: str = Field(default="", max_length=1)
    indicativo_negociacao_gravame: str = Field(default="", max_length=1)
    cpf_cnpj_negociador: str = Field(default="", max_length=14)
    indicativo_saldo_aberto: str = Field(default="", max_length=1)

    @property
    def bandeira_descricao(self) -> str:
        return CODIGOS_BANDEIRAS.get(self.bandeira, "Desconhecida")

    @property
    def tipo_liquidacao_descricao(self) -> str:
        return TIPO_LIQUIDACAO.get(self.tipo_liquidacao, "Não identificado")

    @property
    def status_pagamento_descricao(self) -> str:
        return STATUS_PAGAMENTO.get(self.status_pagamento, "Desconhecido")

    @property
    def tipo_lancamento_descricao(self) -> str:
        return TIPOS_LANCAMENTO.get(self.tipo_lancamento, "Desconhecido")


class RegistroDetalhe(BaseRegistro):
    """Registro E - Detalhe do Lançamento"""

    tipo_registro: str = Field(default="E", frozen=True)
    estabelecimento_submissor: str = Field(..., max_length=10)
    bandeira_liquidacao: str = Field(..., max_length=3)
    tipo_liquidacao: str = Field(..., max_length=3)
    parcela: int = Field(..., ge=0, le=99)
    numero_total_parcelas: int = Field(..., ge=0, le=99)
    codigo_autorizacao: str = Field(..., max_length=6)
    tipo_lancamento: str = Field(..., max_length=2)
    chave_ur: str = Field(..., max_length=100)
    codigo_transacao_recebida: str = Field(default="", max_length=22)
    codigo_ajuste: str = Field(default="", max_length=4)
    forma_pagamento: str = Field(..., max_length=3)
    bin_cartao: str = Field(default="", max_length=6)
    numero_cartao: str = Field(default="", max_length=4, description="Últimos 4 dígitos")
    nsu_doc: str = Field(..., max_length=6)
    numero_nota_fiscal: str = Field(default="", max_length=10)
    tid: str = Field(default="", max_length=20)
    codigo_pedido_referencia: str = Field(default="", max_length=20)
    taxa_mdr: Decimal = Field(..., decimal_places=3)
    taxa_recebimento_automatico: Decimal = Field(default=Decimal("0"), decimal_places=3)
    taxa_venda: Decimal = Field(default=Decimal("0"), decimal_places=3)
    sinal_valor_total_venda: str = Field(..., max_length=1)
    valor_total_venda: Decimal = Field(..., decimal_places=2)
    valor_total_venda_original: str = Field(..., max_length=13, description="Valor total venda original do arquivo EDI")
    sinal_valor_bruto: str = Field(..., max_length=1)
    valor_bruto_venda_parcela: Decimal = Field(..., decimal_places=2)
    valor_bruto_original: str = Field(..., max_length=13, description="Valor bruto original do arquivo EDI")
    sinal_valor_liquido: str = Field(..., max_length=1)
    valor_liquido_venda: Decimal = Field(..., decimal_places=2)
    valor_liquido_original: str = Field(..., max_length=13, description="Valor líquido original do arquivo EDI")
    sinal_valor_comissao: str = Field(..., max_length=1)
    valor_comissao: Decimal = Field(..., decimal_places=2)
    valor_comissao_original: str = Field(..., max_length=13, description="Valor comissão original do arquivo EDI")
    hora_transacao: Optional[time] = None
    grupo_cartoes: str = Field(default="", max_length=2)
    bandeira_autorizacao: str = Field(default="", max_length=3)
    codigo_unico_venda: str = Field(default="", max_length=15)
    canal_venda: str = Field(default="", max_length=3)
    numero_terminal: str = Field(default="", max_length=8)
    codigo_modelo_precificacao: str = Field(default="", max_length=5)
    data_autorizacao_venda: Optional[date] = None
    data_captura: Optional[date] = None
    data_lancamento: Optional[date] = None
    data_original_lancamento: Optional[date] = None
    numero_lote: str = Field(default="", max_length=7)
    data_vencimento_original: Optional[date] = None
    matriz_pagamento: str = Field(default="", max_length=10)
    tipo_cartao: str = Field(default="", max_length=2)
    origem_cartao: str = Field(default="", max_length=1)
    arn: str = Field(default="", max_length=23)
    tipo_captura: str = Field(default="", max_length=2)
    cpf_cnpj_recebedor: str = Field(default="", max_length=14)

    @property
    def bandeira_liquidacao_descricao(self) -> str:
        return CODIGOS_BANDEIRAS.get(self.bandeira_liquidacao, "Desconhecida")

    @property
    def tipo_liquidacao_descricao(self) -> str:
        return TIPO_LIQUIDACAO.get(self.tipo_liquidacao, "Não identificado")

    @property
    def tipo_lancamento_descricao(self) -> str:
        return TIPOS_LANCAMENTO.get(self.tipo_lancamento, "Desconhecido")

    @property
    def forma_pagamento_descricao(self) -> str:
        return FORMA_PAGAMENTO.get(self.forma_pagamento, "Desconhecida")

    @property
    def codigo_ajuste_descricao(self) -> str:
        return MOTIVOS_AJUSTE.get(self.codigo_ajuste, "")

    @property
    def grupo_cartoes_descricao(self) -> str:
        return GRUPO_CARTOES.get(self.grupo_cartoes, "")

    @property
    def canal_venda_descricao(self) -> str:
        return CANAL_VENDA.get(self.canal_venda, "")

    @property
    def tipo_cartao_descricao(self) -> str:
        return TIPO_CARTAO.get(self.tipo_cartao, "")

    @property
    def tipo_captura_descricao(self) -> str:
        return TIPO_CAPTURA.get(self.tipo_captura, "")

    @property
    def codigo_modelo_precificacao_descricao(self) -> str:
        return TIPO_PRECIFICACAO.get(self.codigo_modelo_precificacao, "")


class RegistroPix(BaseRegistro):
    """Registro 8 - Detalhe Transação Pix"""

    tipo_registro: str = Field(default="8", frozen=True)
    estabelecimento_submissor: str = Field(..., max_length=10)
    tipo_transacao: str = Field(..., max_length=2)
    data_transacao: Optional[date] = None
    hora_transacao: Optional[time] = None
    id_pix: str = Field(..., max_length=36)
    nsu_doc: str = Field(..., max_length=6)
    data_pagamento: Optional[date] = None
    sinal_valor_bruto: str = Field(..., max_length=1)
    valor_bruto: Decimal = Field(..., decimal_places=2)
    valor_bruto_original: str = Field(..., max_length=13, description="Valor bruto original do arquivo EDI")
    sinal_taxa_administrativa: str = Field(..., max_length=1)
    valor_taxa_administrativa: Decimal = Field(..., decimal_places=2)
    valor_taxa_administrativa_original: str = Field(..., max_length=13, description="Valor taxa original do arquivo EDI")
    sinal_valor_liquido: str = Field(..., max_length=1)
    valor_liquido: Decimal = Field(..., decimal_places=2)
    valor_liquido_original: str = Field(..., max_length=13, description="Valor líquido original do arquivo EDI")
    banco: str = Field(..., max_length=4)
    agencia: str = Field(..., max_length=5)
    conta: str = Field(..., max_length=20)
    data_captura_transacao: Optional[date] = None
    taxa_administrativa: Decimal = Field(default=Decimal("0"), decimal_places=2)
    tarifa_administrativa: Decimal = Field(default=Decimal("0"), decimal_places=2)
    canal_venda: str = Field(default="", max_length=2)
    numero_logico_terminal: str = Field(default="", max_length=8)
    tx_id: str = Field(default="", max_length=36)

    @property
    def canal_venda_descricao(self) -> str:
        return CANAL_VENDA.get(self.canal_venda, "")


class RegistroNegociacaoResumo(BaseRegistro):
    """Registro A - Resumo de Negociação"""

    tipo_registro: str = Field(default="A", frozen=True)
    data_negociacao: Optional[date] = None
    data_pagamento: Optional[date] = None
    cpf_cnpj: str = Field(..., max_length=14)
    prazo_medio: int = Field(..., ge=0)
    taxa_nominal: Decimal = Field(..., decimal_places=3)
    sinal_valor_bruto: str = Field(..., max_length=1)
    valor_bruto: Decimal = Field(..., decimal_places=2)
    valor_bruto_original: str = Field(default="", max_length=13, description="Valor bruto original do arquivo EDI")
    sinal_valor_liquido: str = Field(..., max_length=1)
    valor_liquido: Decimal = Field(..., decimal_places=2)
    valor_liquido_original: str = Field(default="", max_length=13, description="Valor líquido original do arquivo EDI")
    numero_negociacao_registradora: str = Field(default="", max_length=20)
    forma_pagamento: str = Field(default="", max_length=3)
    taxa_efetiva_negociacao: Decimal = Field(default=Decimal("0"), decimal_places=3)


class RegistroNegociacaoDetalhe(BaseRegistro):
    """Registro B - Detalhe de Negociação"""

    tipo_registro: str = Field(default="B", frozen=True)
    data_negociacao: Optional[date] = None
    data_vencimento_original: Optional[date] = None
    cpf_cnpj: str = Field(..., max_length=14)
    bandeira: str = Field(..., max_length=3)
    tipo_liquidacao: str = Field(default="", max_length=3)
    sinal_valor_bruto: str = Field(..., max_length=1)
    valor_bruto: Decimal = Field(..., decimal_places=2)
    valor_bruto_original: str = Field(default="", max_length=13, description="Valor bruto original do arquivo EDI")
    sinal_valor_liquido: str = Field(..., max_length=1)
    valor_liquido: Decimal = Field(..., decimal_places=2)
    valor_liquido_original: str = Field(default="", max_length=13, description="Valor líquido original do arquivo EDI")
    taxa_efetiva: Decimal = Field(default=Decimal("0"), decimal_places=3)
    instituicao_financeira: str = Field(default="", max_length=50)
    numero_estabelecimento: str = Field(default="", max_length=10)
    sinal_valor_desconto: str = Field(default="", max_length=1)
    valor_desconto: Decimal = Field(default=Decimal("0"), decimal_places=2)
    valor_desconto_original: str = Field(default="", max_length=13, description="Valor desconto original do arquivo EDI")

    @property
    def bandeira_descricao(self) -> str:
        return CODIGOS_BANDEIRAS.get(self.bandeira, "Desconhecida")


class RegistroContaRecebimento(BaseRegistro):
    """Registro C - Conta de Recebimento"""

    tipo_registro: str = Field(default="C", frozen=True)
    banco: str = Field(..., max_length=4)
    agencia: str = Field(..., max_length=5)
    conta: str = Field(..., max_length=20)
    sinal_valor_depositado: str = Field(..., max_length=1)
    valor_depositado: Decimal = Field(..., decimal_places=2)
    valor_depositado_original: str = Field(default="", max_length=13, description="Valor depositado original do arquivo EDI")


class RegistroReservaFinanceira(BaseRegistro):
    """Registro R - Reserva Financeira"""

    tipo_registro: str = Field(default="R", frozen=True)
    estabelecimento_submissor: str = Field(..., max_length=10)
    cpf_cnpj_titular_movimento: str = Field(..., max_length=14)
    bandeira: str = Field(..., max_length=3)
    matriz_pagamento: str = Field(..., max_length=10)
    sinal_valor_reserva: str = Field(..., max_length=1)
    valor_reserva: Decimal = Field(..., decimal_places=2)
    valor_reserva_original: str = Field(default="", max_length=13, description="Valor reserva original do arquivo EDI")
    chave_ur: str = Field(..., max_length=100)
    data_vencimento_original: Optional[date] = None
    numero_estabelecimento_pagamento: str = Field(default="", max_length=10)

    @property
    def bandeira_descricao(self) -> str:
        return CODIGOS_BANDEIRAS.get(self.bandeira, "Desconhecida")


class RegistroTrailer(BaseRegistro):
    """Registro 9 - Trailer do arquivo"""

    tipo_registro: str = Field(default="9", frozen=True)
    total_registros: int = Field(..., ge=0)
    sinal_valor_liquido: str = Field(..., max_length=1)
    valor_liquido_soma: Decimal = Field(..., decimal_places=2)
    valor_liquido_soma_original: str = Field(default="", max_length=17, description="Valor líquido soma original do arquivo EDI")
    quantidade_registro_e: int = Field(..., ge=0)
    sinal_valor_bruto: str = Field(..., max_length=1)
    valor_bruto_soma: Decimal = Field(..., decimal_places=2)
    valor_bruto_soma_original: str = Field(default="", max_length=17, description="Valor bruto soma original do arquivo EDI")
    sinal_valor_liquido_cedido: str = Field(default="", max_length=1)
    valor_liquido_cedido: Decimal = Field(default=Decimal("0"), decimal_places=2)
    valor_liquido_cedido_original: str = Field(default="", max_length=17, description="Valor líquido cedido original do arquivo EDI")
    sinal_valor_liquido_gravame: str = Field(default="", max_length=1)
    valor_liquido_gravame: Decimal = Field(default=Decimal("0"), decimal_places=2)
    valor_liquido_gravame_original: str = Field(default="", max_length=17, description="Valor líquido gravame original do arquivo EDI")


class Estatisticas(BaseModel):
    """Estatísticas do processamento do arquivo"""

    total_linhas: int = 0
    total_ur_agenda: int = 0
    total_detalhes: int = 0
    total_pix: int = 0
    total_negociacoes: int = 0
    valor_bruto_total: Decimal = Decimal("0")
    valor_liquido_total: Decimal = Decimal("0")

    @field_serializer('*', when_used='json')
    def serialize_decimal_as_float(self, value: Any) -> Any:
        """Serializa campos Decimal como float no JSON"""
        if isinstance(value, Decimal):
            return float(value)
        return value


class LinhaErro(BaseModel):
    """Registro de linha não processada ou com erro"""

    linha: int
    tipo: str
    erro: Optional[str] = None
    conteudo: str


class ResultadoProcessamento(BaseModel):
    """Resultado completo do processamento de um arquivo EDI"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    header: Optional[RegistroHeader] = None
    tipo_arquivo: Optional[str] = None
    tipo_arquivo_descricao: Optional[str] = None
    ur_agenda: List[RegistroURAgenda] = Field(default_factory=list)
    detalhes: List[RegistroDetalhe] = Field(default_factory=list)
    pix: List[RegistroPix] = Field(default_factory=list)
    negociacoes_resumo: List[RegistroNegociacaoResumo] = Field(default_factory=list)
    negociacoes_detalhe: List[RegistroNegociacaoDetalhe] = Field(default_factory=list)
    contas_recebimento: List[RegistroContaRecebimento] = Field(default_factory=list)
    reserva_financeira: List[RegistroReservaFinanceira] = Field(default_factory=list)
    trailer: Optional[RegistroTrailer] = None
    estatisticas: Estatisticas = Field(default_factory=Estatisticas)
    linhas_nao_processadas: List[LinhaErro] = Field(default_factory=list)

    def to_dict(self, include_descriptions: bool = True) -> Dict[str, Any]:
        """
        Converte resultado para dicionário.

        Args:
            include_descriptions: Se True, inclui descrições dos códigos

        Returns:
            Dicionário com todos os dados
        """
        data = self.model_dump(mode="json")

        if include_descriptions and self.tipo_arquivo:
            data["tipo_arquivo_descricao"] = TIPOS_ARQUIVO.get(
                self.tipo_arquivo, "Desconhecido"
            )

        return data
