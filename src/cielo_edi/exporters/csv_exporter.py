import csv
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Union

from cielo_edi.models import ResultadoProcessamento

RecordType = Literal[
    "ur_agenda", "detalhes", "pix", "negociacoes_resumo",
    "negociacoes_detalhe", "contas_recebimento", "reserva_financeira"
]


class CSVExporter:
    """
    Exporta ResultadoProcessamento para CSV.

    Como CSV é tabular, cada tipo de registro deve ser exportado separadamente.

    Exemplos:
        >>> exporter = CSVExporter()
        >>> csv_str = exporter.exportar(resultado, "detalhes")
        >>> exporter.exportar_arquivo(resultado, "detalhes", "detalhes.csv")
        >>> exporter.exportar_todos(resultado, "pasta_saida/")
    """

    def __init__(
            self,
            delimiter: str = ";",
            quotechar: str = '"',
            encoding: str = "utf-8-sig",  # BOM para Excel
    ):
        """
        Inicializa o exportador.

        Args:
            delimiter: Delimitador de campos
            quotechar: Caractere de aspas
            encoding: Encoding do arquivo (utf-8-sig inclui BOM para Excel)
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding

    def _converter_valor(self, valor: Any) -> str:
        """Converte valor para string CSV."""
        if valor is None:
            return ""
        if isinstance(valor, Decimal):
            return str(float(valor))
        if isinstance(valor, bool):
            return "1" if valor else "0"
        return str(valor)

    def _registros_para_lista(self, registros: List[Any]) -> List[Dict[str, Any]]:
        """Converte lista de registros Pydantic para lista de dicts."""
        if not registros:
            return []
        return [r.model_dump(mode="json") for r in registros]

    def exportar(
            self,
            resultado: ResultadoProcessamento,
            tipo_registro: RecordType,
    ) -> str:
        """
        Exporta um tipo de registro para string CSV.

        Args:
            resultado: Resultado do processamento
            tipo_registro: Tipo de registro a exportar

        Returns:
            String CSV formatada
        """
        registros = getattr(resultado, tipo_registro, [])
        dados = self._registros_para_lista(registros)

        if not dados:
            return ""

        output = StringIO()
        fieldnames = list(dados[0].keys())

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writeheader()
        for row in dados:
            writer.writerow({k: self._converter_valor(v) for k, v in row.items()})

        return output.getvalue()

    def exportar_arquivo(
            self,
            resultado: ResultadoProcessamento,
            tipo_registro: RecordType,
            caminho: Union[str, Path],
    ) -> None:
        """
        Exporta um tipo de registro para arquivo CSV.

        Args:
            resultado: Resultado do processamento
            tipo_registro: Tipo de registro a exportar
            caminho: Caminho do arquivo de saída
        """
        caminho = Path(caminho)
        csv_str = self.exportar(resultado, tipo_registro)

        # newline='' é necessário no Windows para evitar linhas em branco extras
        with open(caminho, 'w', encoding=self.encoding, newline='') as f:
            f.write(csv_str)

    def exportar_todos(
            self,
            resultado: ResultadoProcessamento,
            diretorio: Union[str, Path],
            prefixo: str = "",
    ) -> Dict[str, Path]:
        """
        Exporta todos os tipos de registro para arquivos CSV separados.

        Args:
            resultado: Resultado do processamento
            diretorio: Diretório de saída
            prefixo: Prefixo para nomes de arquivos

        Returns:
            Dicionário com tipo -> caminho do arquivo criado
        """
        diretorio = Path(diretorio)
        diretorio.mkdir(parents=True, exist_ok=True)

        arquivos_criados: Dict[str, Path] = {}

        tipos: List[RecordType] = [
            "ur_agenda",
            "detalhes",
            "pix",
            "negociacoes_resumo",
            "negociacoes_detalhe",
            "contas_recebimento",
            "reserva_financeira",
        ]

        for tipo in tipos:
            registros = getattr(resultado, tipo, [])
            if registros:
                nome_arquivo = f"{prefixo}{tipo}.csv" if prefixo else f"{tipo}.csv"
                caminho = diretorio / nome_arquivo
                self.exportar_arquivo(resultado, tipo, caminho)
                arquivos_criados[tipo] = caminho

        return arquivos_criados
