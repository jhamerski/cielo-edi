"""
Interface de linha de comando para o parser Cielo EDI.

Uso:
    cielo-edi arquivo.txt -o resultado.json
    cielo-edi arquivo.txt --formato csv --diretorio ./saida
    cielo-edi arquivo.txt --info
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from cielo_edi import __version__
from cielo_edi.parser import CieloEDIParser
from cielo_edi.exporters.json_exporter import JSONExporter
from cielo_edi.exporters.csv_exporter import CSVExporter


def configurar_logging(verbose: bool) -> None:
    """Configura o logging baseado no nível de verbosidade."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def criar_parser_args() -> argparse.ArgumentParser:
    """Cria o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="cielo-edi",
        description="Parser para arquivos Cielo EDI - Extrato Eletrônico",
        epilog="Exemplo: cielo-edi CIELO04_20241218.txt -o resultado.json",
    )

    parser.add_argument(
        "arquivo",
        type=Path,
        help="Caminho do arquivo EDI para processar",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Caminho do arquivo de saída (padrão: mesmo nome com extensão .json)",
    )

    parser.add_argument(
        "-f", "--formato",
        choices=["json", "csv"],
        default="json",
        help="Formato de saída (padrão: json)",
    )

    parser.add_argument(
        "-d", "--diretorio",
        type=Path,
        help="Diretório para arquivos CSV (usado apenas com --formato csv)",
    )

    parser.add_argument(
        "-e", "--encoding",
        default="latin-1",
        help="Encoding do arquivo de entrada (padrão: latin-1)",
    )

    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentação do JSON (padrão: 2, use 0 para minificado)",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Exibe apenas informações resumidas do arquivo",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verboso com logs detalhados",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def exibir_info(resultado: "ResultadoProcessamento") -> None:
    """Exibe informações resumidas do processamento."""
    print("\n" + "=" * 60)
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 60)

    if resultado.header:
        print(f"Estabelecimento: {resultado.header.estabelecimento_matriz}")
        print(f"Data Processamento: {resultado.header.data_processamento}")
        print(f"Período: {resultado.header.periodo_inicial} a {resultado.header.periodo_final}")
        print(f"Versão Layout: {resultado.header.versao_layout}")

    print(f"\nTipo de Arquivo: {resultado.tipo_arquivo_descricao} ({resultado.tipo_arquivo})")
    print(f"\nEstatísticas:")
    print(f"  Total de Linhas: {resultado.estatisticas.total_linhas:,}")
    print(f"  URs Agenda: {resultado.estatisticas.total_ur_agenda:,}")
    print(f"  Detalhes: {resultado.estatisticas.total_detalhes:,}")
    print(f"  Transações Pix: {resultado.estatisticas.total_pix:,}")
    print(f"  Negociações: {resultado.estatisticas.total_negociacoes:,}")
    print(f"\nValores:")
    print(f"  Valor Bruto Total: R$ {resultado.estatisticas.valor_bruto_total:,.2f}")
    print(f"  Valor Líquido Total: R$ {resultado.estatisticas.valor_liquido_total:,.2f}")

    if resultado.linhas_nao_processadas:
        print(f"\n⚠ Linhas não processadas: {len(resultado.linhas_nao_processadas)}")

    print("=" * 60)


def main(args: Optional[list] = None) -> int:
    """Função principal da CLI."""
    parser = criar_parser_args()
    parsed_args = parser.parse_args(args)

    configurar_logging(parsed_args.verbose)
    logger = logging.getLogger(__name__)

    # Validar arquivo de entrada
    if not parsed_args.arquivo.exists():
        print(f"Erro: Arquivo não encontrado: {parsed_args.arquivo}", file=sys.stderr)
        return 1

    try:
        # Processar arquivo
        logger.info(f"Processando: {parsed_args.arquivo}")
        edi_parser = CieloEDIParser(encoding=parsed_args.encoding)
        resultado = edi_parser.processar_arquivo(parsed_args.arquivo)

        # Modo info apenas
        if parsed_args.info:
            exibir_info(resultado)
            return 0

        # Exportar resultado
        if parsed_args.formato == "json":
            indent = parsed_args.indent if parsed_args.indent > 0 else None
            exporter = JSONExporter(indent=indent)

            if parsed_args.output:
                caminho_saida = parsed_args.output
            else:
                caminho_saida = parsed_args.arquivo.with_suffix(".json")

            exporter.exportar_arquivo(resultado, caminho_saida)
            print(f"✓ Arquivo JSON salvo em: {caminho_saida}")

        elif parsed_args.formato == "csv":
            exporter = CSVExporter()

            if parsed_args.diretorio:
                diretorio = parsed_args.diretorio
            else:
                diretorio = parsed_args.arquivo.parent / f"{parsed_args.arquivo.stem}_csv"

            arquivos = exporter.exportar_todos(
                resultado,
                diretorio,
                prefixo=f"{parsed_args.arquivo.stem}_",
            )

            print(f"✓ Arquivos CSV salvos em: {diretorio}")
            for tipo, caminho in arquivos.items():
                print(f"  - {caminho.name}")

        # Sempre exibir resumo
        exibir_info(resultado)

        return 0

    except Exception as e:
        logger.exception(f"Erro ao processar arquivo: {e}")
        print(f"Erro: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
