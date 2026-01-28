"""
Parser principal para arquivos Cielo EDI.

Suporta todos os tipos de arquivo: CIELO03, CIELO04, CIELO09, CIELO15, CIELO16.
"""

import logging
from datetime import date, time
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterator, Optional, Union

from cielo_edi.dominios import TIPOS_ARQUIVO
from cielo_edi.models import (
    LinhaErro,
    RegistroContaRecebimento,
    RegistroDetalhe,
    RegistroHeader,
    RegistroNegociacaoDetalhe,
    RegistroNegociacaoResumo,
    RegistroPix,
    RegistroReservaFinanceira,
    RegistroTrailer,
    RegistroURAgenda,
    ResultadoProcessamento,
)

logger = logging.getLogger(__name__)


def extrair_campo(linha: str, inicio: int, fim: int) -> str:
    """Extrai campo da linha conforme posições do manual EDI (1-indexed)."""
    return linha[inicio - 1:fim].strip()


def converter_valor_decimal(valor: str, casas_decimais: int = 2) -> Decimal:
    """Converte valores monetários conforme regra EDI (sem separador decimal)."""
    if not valor or valor.strip() == "":
        return Decimal("0")
    try:
        valor_limpo = valor.strip()
        if valor_limpo:
            return Decimal(valor_limpo) / Decimal(10 ** casas_decimais)
    except (ValueError, TypeError):
        return Decimal("0")
    return Decimal("0")


def converter_data(data_str: str, formato: str = "DDMMAAAA") -> Optional[date]:
    """Converte data do formato EDI para objeto date."""
    if not data_str or data_str.strip() in ("", "01011001", "00000000"):
        return None

    try:
        data_limpa = data_str.strip()

        if formato == "DDMMAAAA" and len(data_limpa) == 8:
            return date(int(data_limpa[4:8]), int(data_limpa[2:4]), int(data_limpa[0:2]))
        elif formato == "AAAAMMDD" and len(data_limpa) == 8:
            return date(int(data_limpa[0:4]), int(data_limpa[4:6]), int(data_limpa[6:8]))
        elif formato == "AAMMDD" and len(data_limpa) == 6:
            return date(int(f"20{data_limpa[0:2]}"), int(data_limpa[2:4]), int(data_limpa[4:6]))
    except (ValueError, TypeError):
        pass
    return None


def converter_hora(hora_str: str) -> Optional[time]:
    """Converte hora de HHMMSS para objeto time."""
    if not hora_str or len(hora_str.strip()) != 6:
        return None
    try:
        h = hora_str.strip()
        return time(int(h[0:2]), int(h[2:4]), int(h[4:6]))
    except (ValueError, TypeError):
        return None


def parse_registro_header(linha: str) -> RegistroHeader:
    """Parse do Registro 0 - Header"""
    return RegistroHeader(
        tipo_registro=extrair_campo(linha, 1, 1),
        estabelecimento_matriz=extrair_campo(linha, 2, 11),
        data_processamento=converter_data(extrair_campo(linha, 12, 19), "AAAAMMDD"),
        periodo_inicial=converter_data(extrair_campo(linha, 20, 27), "AAAAMMDD"),
        periodo_final=converter_data(extrair_campo(linha, 28, 35), "AAAAMMDD"),
        sequencia=extrair_campo(linha, 36, 42),
        empresa_adquirente=extrair_campo(linha, 43, 47),
        opcao_extrato=extrair_campo(linha, 48, 49),
        transmissao=extrair_campo(linha, 50, 50),
        caixa_postal=extrair_campo(linha, 51, 70),
        versao_layout=extrair_campo(linha, 71, 73),
    )


def parse_registro_ur_agenda(linha: str) -> RegistroURAgenda:
    """Parse do Registro D - UR Agenda"""
    # Extrair valores originais antes da conversão
    valor_bruto_original = extrair_campo(linha, 73, 85)
    valor_taxa_administrativa_original = extrair_campo(linha, 87, 99)
    valor_liquido_original = extrair_campo(linha, 101, 113)

    return RegistroURAgenda(
        tipo_registro=extrair_campo(linha, 1, 1),
        estabelecimento_submissor=extrair_campo(linha, 2, 11),
        cpf_cnpj_titular=extrair_campo(linha, 12, 25),
        cpf_cnpj_titular_movimento=extrair_campo(linha, 26, 39),
        cpf_cnpj_recebedor=extrair_campo(linha, 40, 53),
        bandeira=extrair_campo(linha, 54, 56),
        tipo_liquidacao=extrair_campo(linha, 57, 59),
        matriz_pagamento=extrair_campo(linha, 60, 69),
        status_pagamento=extrair_campo(linha, 70, 71),
        sinal_valor_bruto=extrair_campo(linha, 72, 72),
        valor_bruto=converter_valor_decimal(valor_bruto_original, 2),
        valor_bruto_original=valor_bruto_original,
        sinal_taxa_administrativa=extrair_campo(linha, 86, 86),
        valor_taxa_administrativa=converter_valor_decimal(valor_taxa_administrativa_original, 2),
        valor_taxa_administrativa_original=valor_taxa_administrativa_original,
        sinal_valor_liquido=extrair_campo(linha, 100, 100),
        valor_liquido=converter_valor_decimal(valor_liquido_original, 2),
        valor_liquido_original=valor_liquido_original,
        banco=extrair_campo(linha, 114, 117),
        agencia=extrair_campo(linha, 118, 122),
        conta=extrair_campo(linha, 123, 142),
        digito_conta=extrair_campo(linha, 143, 143),
        quantidade_lancamentos=int(extrair_campo(linha, 144, 149) or 0),
        tipo_lancamento=extrair_campo(linha, 150, 151),
        chave_ur=extrair_campo(linha, 152, 251),
        data_pagamento=converter_data(extrair_campo(linha, 268, 275), "DDMMAAAA"),
        data_envio_banco=converter_data(extrair_campo(linha, 276, 283), "DDMMAAAA"),
        data_vencimento_original=converter_data(extrair_campo(linha, 284, 291), "DDMMAAAA"),
        numero_estabelecimento_pagamento=extrair_campo(linha, 292, 301),
        indicativo_lancamento_pendente=extrair_campo(linha, 302, 302),
        indicativo_reenvio_pagamento=extrair_campo(linha, 303, 303),
        indicativo_negociacao_gravame=extrair_campo(linha, 304, 304),
        cpf_cnpj_negociador=extrair_campo(linha, 305, 318),
        indicativo_saldo_aberto=extrair_campo(linha, 319, 319),
    )


def parse_registro_detalhe(linha: str) -> RegistroDetalhe:
    """Parse do Registro E - Detalhe do Lançamento"""
    # Extrair valores originais antes da conversão
    valor_total_venda_original = extrair_campo(linha, 248, 260)
    valor_bruto_original = extrair_campo(linha, 262, 274)
    valor_liquido_original = extrair_campo(linha, 276, 288)
    valor_comissao_original = extrair_campo(linha, 290, 302)

    return RegistroDetalhe(
        tipo_registro=extrair_campo(linha, 1, 1),
        estabelecimento_submissor=extrair_campo(linha, 2, 11),
        bandeira_liquidacao=extrair_campo(linha, 12, 14),
        tipo_liquidacao=extrair_campo(linha, 15, 17),
        parcela=int(extrair_campo(linha, 18, 19) or 0),
        numero_total_parcelas=int(extrair_campo(linha, 20, 21) or 0),
        codigo_autorizacao=extrair_campo(linha, 22, 27),
        tipo_lancamento=extrair_campo(linha, 28, 29),
        chave_ur=extrair_campo(linha, 30, 129),
        codigo_transacao_recebida=extrair_campo(linha, 130, 151),
        codigo_ajuste=extrair_campo(linha, 152, 155),
        forma_pagamento=extrair_campo(linha, 156, 158),
        bin_cartao=extrair_campo(linha, 166, 171),
        numero_cartao=extrair_campo(linha, 172, 175),
        nsu_doc=extrair_campo(linha, 176, 181),
        numero_nota_fiscal=extrair_campo(linha, 182, 191),
        tid=extrair_campo(linha, 192, 211),
        codigo_pedido_referencia=extrair_campo(linha, 212, 231),
        taxa_mdr=converter_valor_decimal(extrair_campo(linha, 232, 236), 3),
        taxa_recebimento_automatico=converter_valor_decimal(extrair_campo(linha, 237, 241), 3),
        taxa_venda=converter_valor_decimal(extrair_campo(linha, 242, 246), 3),
        sinal_valor_total_venda=extrair_campo(linha, 247, 247),
        valor_total_venda=converter_valor_decimal(valor_total_venda_original, 2),
        valor_total_venda_original=valor_total_venda_original,
        sinal_valor_bruto=extrair_campo(linha, 261, 261),
        valor_bruto_venda_parcela=converter_valor_decimal(valor_bruto_original, 2),
        valor_bruto_original=valor_bruto_original,
        sinal_valor_liquido=extrair_campo(linha, 275, 275),
        valor_liquido_venda=converter_valor_decimal(valor_liquido_original, 2),
        valor_liquido_original=valor_liquido_original,
        sinal_valor_comissao=extrair_campo(linha, 289, 289),
        valor_comissao=converter_valor_decimal(valor_comissao_original, 2),
        valor_comissao_original=valor_comissao_original,
        hora_transacao=converter_hora(extrair_campo(linha, 471, 476)),
        grupo_cartoes=extrair_campo(linha, 477, 478),
        cpf_cnpj_recebedor=extrair_campo(linha, 479, 492),
        bandeira_autorizacao=extrair_campo(linha, 493, 495),
        codigo_unico_venda=extrair_campo(linha, 496, 510),
        canal_venda=extrair_campo(linha, 541, 543),
        numero_terminal=extrair_campo(linha, 544, 551),
        codigo_modelo_precificacao=extrair_campo(linha, 561, 565),
        data_autorizacao_venda=converter_data(extrair_campo(linha, 566, 573), "DDMMAAAA"),
        data_captura=converter_data(extrair_campo(linha, 574, 581), "DDMMAAAA"),
        data_lancamento=converter_data(extrair_campo(linha, 582, 589), "DDMMAAAA"),
        data_original_lancamento=converter_data(extrair_campo(linha, 590, 597), "DDMMAAAA"),
        numero_lote=extrair_campo(linha, 598, 604),
        data_vencimento_original=converter_data(extrair_campo(linha, 630, 637), "DDMMAAAA"),
        matriz_pagamento=extrair_campo(linha, 638, 647),
        tipo_cartao=extrair_campo(linha, 648, 649),
        origem_cartao=extrair_campo(linha, 650, 650),
        arn=extrair_campo(linha, 683, 705),
        tipo_captura=extrair_campo(linha, 707, 708),
    )


def parse_registro_pix(linha: str) -> RegistroPix:
    """Parse do Registro 8 - Transação Pix"""
    # Extrair valores originais antes da conversão
    valor_bruto_original = extrair_campo(linha, 75, 87)
    valor_taxa_administrativa_original = extrair_campo(linha, 89, 101)
    valor_liquido_original = extrair_campo(linha, 103, 115)

    return RegistroPix(
        tipo_registro=extrair_campo(linha, 1, 1),
        estabelecimento_submissor=extrair_campo(linha, 2, 11),
        tipo_transacao=extrair_campo(linha, 12, 13),
        data_transacao=converter_data(extrair_campo(linha, 14, 19), "AAMMDD"),
        hora_transacao=converter_hora(extrair_campo(linha, 20, 25)),
        id_pix=extrair_campo(linha, 26, 61),
        nsu_doc=extrair_campo(linha, 62, 67),
        data_pagamento=converter_data(extrair_campo(linha, 68, 73), "AAMMDD"),
        sinal_valor_bruto=extrair_campo(linha, 74, 74),
        valor_bruto=converter_valor_decimal(valor_bruto_original, 2),
        valor_bruto_original=valor_bruto_original,
        sinal_taxa_administrativa=extrair_campo(linha, 88, 88),
        valor_taxa_administrativa=converter_valor_decimal(valor_taxa_administrativa_original, 2),
        valor_taxa_administrativa_original=valor_taxa_administrativa_original,
        sinal_valor_liquido=extrair_campo(linha, 102, 102),
        valor_liquido=converter_valor_decimal(valor_liquido_original, 2),
        valor_liquido_original=valor_liquido_original,
        banco=extrair_campo(linha, 116, 119),
        agencia=extrair_campo(linha, 120, 124),
        conta=extrair_campo(linha, 125, 144),
        data_captura_transacao=converter_data(extrair_campo(linha, 145, 150), "AAMMDD"),
        taxa_administrativa=converter_valor_decimal(extrair_campo(linha, 151, 155), 2),
        tarifa_administrativa=converter_valor_decimal(extrair_campo(linha, 156, 159), 2),
        canal_venda=extrair_campo(linha, 160, 161),
        numero_logico_terminal=extrair_campo(linha, 162, 169),
        tx_id=extrair_campo(linha, 240, 275),
    )


def parse_registro_negociacao_resumo(linha: str) -> RegistroNegociacaoResumo:
    """Parse do Registro A - Resumo Negociação"""
    # Extrair valores originais antes da conversão
    valor_bruto_original = extrair_campo(linha, 37, 49)
    valor_liquido_original = extrair_campo(linha, 51, 63)

    return RegistroNegociacaoResumo(
        tipo_registro=extrair_campo(linha, 1, 1),
        data_negociacao=converter_data(extrair_campo(linha, 2, 7), "AAMMDD"),
        data_pagamento=converter_data(extrair_campo(linha, 8, 13), "AAMMDD"),
        cpf_cnpj=extrair_campo(linha, 14, 27),
        prazo_medio=int(extrair_campo(linha, 28, 30) or 0),
        taxa_nominal=converter_valor_decimal(extrair_campo(linha, 31, 35), 3),
        sinal_valor_bruto=extrair_campo(linha, 36, 36),
        valor_bruto=converter_valor_decimal(valor_bruto_original, 2),
        valor_bruto_original=valor_bruto_original,
        sinal_valor_liquido=extrair_campo(linha, 50, 50),
        valor_liquido=converter_valor_decimal(valor_liquido_original, 2),
        valor_liquido_original=valor_liquido_original,
        numero_negociacao_registradora=extrair_campo(linha, 64, 83),
        forma_pagamento=extrair_campo(linha, 84, 86),
        taxa_efetiva_negociacao=converter_valor_decimal(extrair_campo(linha, 87, 91), 3),
    )


def parse_registro_negociacao_detalhe(linha: str) -> RegistroNegociacaoDetalhe:
    """Parse do Registro B - Detalhe Negociação"""
    # Extrair valores originais antes da conversão
    valor_bruto_original = extrair_campo(linha, 35, 47)
    valor_liquido_original = extrair_campo(linha, 49, 61)
    valor_desconto_original = extrair_campo(linha, 128, 140)

    return RegistroNegociacaoDetalhe(
        tipo_registro=extrair_campo(linha, 1, 1),
        data_negociacao=converter_data(extrair_campo(linha, 2, 7), "AAMMDD"),
        data_vencimento_original=converter_data(extrair_campo(linha, 8, 13), "AAMMDD"),
        cpf_cnpj=extrair_campo(linha, 14, 27),
        bandeira=extrair_campo(linha, 28, 30),
        tipo_liquidacao=extrair_campo(linha, 31, 33),
        sinal_valor_bruto=extrair_campo(linha, 34, 34),
        valor_bruto=converter_valor_decimal(valor_bruto_original, 2),
        valor_bruto_original=valor_bruto_original,
        sinal_valor_liquido=extrair_campo(linha, 48, 48),
        valor_liquido=converter_valor_decimal(valor_liquido_original, 2),
        valor_liquido_original=valor_liquido_original,
        taxa_efetiva=converter_valor_decimal(extrair_campo(linha, 62, 66), 3),
        instituicao_financeira=extrair_campo(linha, 67, 116),
        numero_estabelecimento=extrair_campo(linha, 117, 126),
        sinal_valor_desconto=extrair_campo(linha, 127, 127),
        valor_desconto=converter_valor_decimal(valor_desconto_original, 2),
        valor_desconto_original=valor_desconto_original,
    )


def parse_registro_conta_recebimento(linha: str) -> RegistroContaRecebimento:
    """Parse do Registro C - Conta de Recebimento"""
    # Extrair valores originais antes da conversão
    valor_depositado_original = extrair_campo(linha, 32, 44)

    return RegistroContaRecebimento(
        tipo_registro=extrair_campo(linha, 1, 1),
        banco=extrair_campo(linha, 2, 5),
        agencia=extrair_campo(linha, 6, 10),
        conta=extrair_campo(linha, 11, 30),
        sinal_valor_depositado=extrair_campo(linha, 31, 31),
        valor_depositado=converter_valor_decimal(valor_depositado_original, 2),
        valor_depositado_original=valor_depositado_original,
    )


def parse_registro_reserva_financeira(linha: str) -> RegistroReservaFinanceira:
    """Parse do Registro R - Reserva Financeira"""
    # Extrair valores originais antes da conversão
    valor_reserva_original = extrair_campo(linha, 40, 52)

    return RegistroReservaFinanceira(
        tipo_registro=extrair_campo(linha, 1, 1),
        estabelecimento_submissor=extrair_campo(linha, 2, 11),
        cpf_cnpj_titular_movimento=extrair_campo(linha, 12, 25),
        bandeira=extrair_campo(linha, 26, 28),
        matriz_pagamento=extrair_campo(linha, 29, 38),
        sinal_valor_reserva=extrair_campo(linha, 39, 39),
        valor_reserva=converter_valor_decimal(valor_reserva_original, 2),
        valor_reserva_original=valor_reserva_original,
        chave_ur=extrair_campo(linha, 53, 152),
        data_vencimento_original=converter_data(extrair_campo(linha, 153, 160), "DDMMAAAA"),
        numero_estabelecimento_pagamento=extrair_campo(linha, 161, 170),
    )


def parse_registro_trailer(linha: str) -> RegistroTrailer:
    """Parse do Registro 9 - Trailer"""
    # Extrair valores originais antes da conversão
    valor_liquido_soma_original = extrair_campo(linha, 14, 30)
    valor_bruto_soma_original = extrair_campo(linha, 43, 59)
    valor_liquido_cedido_original = extrair_campo(linha, 61, 77)
    valor_liquido_gravame_original = extrair_campo(linha, 79, 95)

    return RegistroTrailer(
        tipo_registro=extrair_campo(linha, 1, 1),
        total_registros=int(extrair_campo(linha, 2, 12) or 0),
        sinal_valor_liquido=extrair_campo(linha, 13, 13),
        valor_liquido_soma=converter_valor_decimal(valor_liquido_soma_original, 2),
        valor_liquido_soma_original=valor_liquido_soma_original,
        quantidade_registro_e=int(extrair_campo(linha, 31, 41) or 0),
        sinal_valor_bruto=extrair_campo(linha, 42, 42),
        valor_bruto_soma=converter_valor_decimal(valor_bruto_soma_original, 2),
        valor_bruto_soma_original=valor_bruto_soma_original,
        sinal_valor_liquido_cedido=extrair_campo(linha, 60, 60),
        valor_liquido_cedido=converter_valor_decimal(valor_liquido_cedido_original, 2),
        valor_liquido_cedido_original=valor_liquido_cedido_original,
        sinal_valor_liquido_gravame=extrair_campo(linha, 78, 78),
        valor_liquido_gravame=converter_valor_decimal(valor_liquido_gravame_original, 2),
        valor_liquido_gravame_original=valor_liquido_gravame_original,
    )


PARSERS: Dict[str, Callable[[str], Any]] = {
    "0": parse_registro_header,
    "D": parse_registro_ur_agenda,
    "E": parse_registro_detalhe,
    "8": parse_registro_pix,
    "A": parse_registro_negociacao_resumo,
    "B": parse_registro_negociacao_detalhe,
    "C": parse_registro_conta_recebimento,
    "R": parse_registro_reserva_financeira,
    "9": parse_registro_trailer,
}


class CieloEDIParser:
    """
    Parser completo para arquivos Cielo EDI.

    Suporta múltiplas fontes de entrada: arquivo, string, bytes ou file-like object.

    Exemplos:
        >>> parser = CieloEDIParser()
        >>> resultado = parser.processar("/caminho/arquivo.txt")
        >>> resultado = parser.processar_string(conteudo_edi)
        >>> for registro in parser.processar_streaming("/caminho/arquivo.txt"):
        ...     print(registro)
    """

    def __init__(self, encoding: str = "latin-1"):
        self.encoding = encoding
        self._parsers = PARSERS

    def processar(self, fonte: Union[str, Path, IO[str], bytes]) -> ResultadoProcessamento:
        """Processa um arquivo EDI de qualquer fonte."""
        if isinstance(fonte, bytes):
            return self.processar_bytes(fonte)
        elif isinstance(fonte, (str, Path)):
            return self.processar_arquivo(fonte)
        else:
            return self._processar_io(fonte)

    def processar_arquivo(self, caminho: Union[str, Path]) -> ResultadoProcessamento:
        """Processa arquivo EDI a partir do caminho."""
        caminho = Path(caminho)
        logger.info(f"Processando arquivo: {caminho}")

        with open(caminho, "r", encoding=self.encoding) as arquivo:
            return self._processar_io(arquivo)

    def processar_string(self, conteudo: str) -> ResultadoProcessamento:
        """Processa conteúdo EDI a partir de string."""
        return self._processar_io(StringIO(conteudo))

    def processar_bytes(self, dados: bytes) -> ResultadoProcessamento:
        """Processa conteúdo EDI a partir de bytes."""
        conteudo = dados.decode(self.encoding)
        return self.processar_string(conteudo)

    def processar_streaming(self, fonte: Union[str, Path, IO[str]]) -> Iterator[Any]:
        """Processa arquivo em modo streaming (linha a linha)."""
        if isinstance(fonte, (str, Path)):
            with open(fonte, "r", encoding=self.encoding) as arquivo:
                yield from self._processar_streaming_io(arquivo)
        else:
            yield from self._processar_streaming_io(fonte)

    def _processar_streaming_io(self, arquivo: IO[str]) -> Iterator[Any]:
        """Processa arquivo em modo streaming."""
        for numero_linha, linha in enumerate(arquivo, 1):
            linha = linha.rstrip("\n\r")
            if not linha:
                continue

            tipo_registro = linha[0] if linha else ""

            if tipo_registro in self._parsers:
                try:
                    yield self._parsers[tipo_registro](linha)
                except Exception as e:
                    logger.warning(f"Erro na linha {numero_linha}: {e}")
                    yield LinhaErro(linha=numero_linha, tipo=tipo_registro, erro=str(e), conteudo=linha[:100])

    def _processar_io(self, arquivo: IO[str]) -> ResultadoProcessamento:
        """Processa conteúdo de um file-like object."""
        resultado = ResultadoProcessamento()

        for numero_linha, linha in enumerate(arquivo, 1):
            linha = linha.rstrip("\n\r")
            resultado.estatisticas.total_linhas += 1

            if not linha:
                continue

            tipo_registro = linha[0] if linha else ""

            try:
                if tipo_registro == "0":
                    resultado.header = parse_registro_header(linha)
                    resultado.tipo_arquivo = resultado.header.opcao_extrato
                    resultado.tipo_arquivo_descricao = TIPOS_ARQUIVO.get(resultado.tipo_arquivo or "", "Desconhecido")

                elif tipo_registro == "D":
                    registro = parse_registro_ur_agenda(linha)
                    resultado.ur_agenda.append(registro)
                    resultado.estatisticas.total_ur_agenda += 1
                    resultado.estatisticas.valor_bruto_total += registro.valor_bruto
                    resultado.estatisticas.valor_liquido_total += registro.valor_liquido

                elif tipo_registro == "E":
                    resultado.detalhes.append(parse_registro_detalhe(linha))
                    resultado.estatisticas.total_detalhes += 1

                elif tipo_registro == "8":
                    resultado.pix.append(parse_registro_pix(linha))
                    resultado.estatisticas.total_pix += 1

                elif tipo_registro == "A":
                    resultado.negociacoes_resumo.append(parse_registro_negociacao_resumo(linha))
                    resultado.estatisticas.total_negociacoes += 1

                elif tipo_registro == "B":
                    resultado.negociacoes_detalhe.append(parse_registro_negociacao_detalhe(linha))

                elif tipo_registro == "C":
                    resultado.contas_recebimento.append(parse_registro_conta_recebimento(linha))

                elif tipo_registro == "R":
                    resultado.reserva_financeira.append(parse_registro_reserva_financeira(linha))

                elif tipo_registro == "9":
                    resultado.trailer = parse_registro_trailer(linha)

                else:
                    resultado.linhas_nao_processadas.append(LinhaErro(linha=numero_linha, tipo=tipo_registro, conteudo=linha[:100]))

            except Exception as e:
                logger.warning(f"Erro ao processar linha {numero_linha}: {e}")
                resultado.linhas_nao_processadas.append(LinhaErro(linha=numero_linha, tipo=tipo_registro, erro=str(e), conteudo=linha[:100]))

        return resultado
