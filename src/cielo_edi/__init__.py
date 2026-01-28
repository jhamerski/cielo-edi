"""
Cielo EDI Parser - Parser para Extrato Eletrônico Cielo

Este pacote fornece ferramentas para parsing e conversão de arquivos
Cielo EDI (Extrato Eletrônico) para formatos estruturados como JSON e CSV.

Suporta todos os tipos de arquivo:
- CIELO03: Captura/Previsão
- CIELO04: Liquidação/Pagamento
- CIELO09: Saldo em Aberto
- CIELO15: Negociação de Recebíveis
- CIELO16: Pix

Exemplos:
    Uso básico:
        >>> from cielo_edi import CieloEDIParser
        >>> parser = CieloEDIParser()
        >>> resultado = parser.processar("arquivo.txt")
        >>> print(resultado.estatisticas.valor_liquido_total)

    Exportar para JSON:
        >>> from cielo_edi import CieloEDIParser, JSONExporter
        >>> parser = CieloEDIParser()
        >>> resultado = parser.processar("arquivo.txt")
        >>> exporter = JSONExporter()
        >>> exporter.exportar_arquivo(resultado, "saida.json")

    Exportar para CSV:
        >>> from cielo_edi import CieloEDIParser, CSVExporter
        >>> parser = CieloEDIParser()
        >>> resultado = parser.processar("arquivo.txt")
        >>> exporter = CSVExporter()
        >>> exporter.exportar_todos(resultado, "./csv_output/")

    Processamento streaming (arquivos grandes):
        >>> from cielo_edi import CieloEDIParser
        >>> parser = CieloEDIParser()
        >>> for registro in parser.processar_streaming("arquivo_grande.txt"):
        ...     processar_registro(registro)

    Via CLI:
        $ cielo-edi arquivo.txt -o resultado.json
        $ cielo-edi arquivo.txt --formato csv --diretorio ./saida
        $ cielo-edi arquivo.txt --info
"""

__version__ = "15.14.1"
__author__ = "Jonas Hamerski"
__email__ = "contato@hathdata.com"

from cielo_edi.parser import CieloEDIParser
from cielo_edi.models import (
    ResultadoProcessamento,
    RegistroHeader,
    RegistroURAgenda,
    RegistroDetalhe,
    RegistroPix,
    RegistroNegociacaoResumo,
    RegistroNegociacaoDetalhe,
    RegistroContaRecebimento,
    RegistroReservaFinanceira,
    RegistroTrailer,
    Estatisticas,
)
from cielo_edi.exporters import JSONExporter, CSVExporter
from cielo_edi.dominios import (
    TIPOS_ARQUIVO,
    TIPOS_LANCAMENTO,
    CODIGOS_BANDEIRAS,
    STATUS_PAGAMENTO,
    FORMA_PAGAMENTO,
    CANAL_VENDA,
    TIPO_CAPTURA,
    TIPO_CARTAO,
)

__all__ = [
    # Versão
    "__version__",
    # Parser principal
    "CieloEDIParser",
    # Modelos
    "ResultadoProcessamento",
    "RegistroHeader",
    "RegistroURAgenda",
    "RegistroDetalhe",
    "RegistroPix",
    "RegistroNegociacaoResumo",
    "RegistroNegociacaoDetalhe",
    "RegistroContaRecebimento",
    "RegistroReservaFinanceira",
    "RegistroTrailer",
    "Estatisticas",
    # Exporters
    "JSONExporter",
    "CSVExporter",
    # Tabelas de domínio
    "TIPOS_ARQUIVO",
    "TIPOS_LANCAMENTO",
    "CODIGOS_BANDEIRAS",
    "STATUS_PAGAMENTO",
    "FORMA_PAGAMENTO",
    "CANAL_VENDA",
    "TIPO_CAPTURA",
    "TIPO_CARTAO",
]
