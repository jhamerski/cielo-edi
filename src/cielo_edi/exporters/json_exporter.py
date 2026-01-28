import json
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Union

from cielo_edi.models import ResultadoProcessamento


class DecimalEncoder(json.JSONEncoder):
    """Encoder customizado para tipos não serializáveis por padrão."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, time)):
            return obj.isoformat()
        return super().default(obj)


class JSONExporter:
    """
    Exporta ResultadoProcessamento para JSON.

    Exemplos:
        >>> exporter = JSONExporter(indent=2, ensure_ascii=False)
        >>> json_str = exporter.exportar(resultado)
        >>> exporter.exportar_arquivo(resultado, "saida.json")
    """

    def __init__(
            self,
            indent: Optional[int] = 2,
            ensure_ascii: bool = False,
            include_descriptions: bool = True,
    ):
        """
        Inicializa o exportador.

        Args:
            indent: Indentação do JSON (None para minificado)
            ensure_ascii: Se True, escapa caracteres não-ASCII
            include_descriptions: Se True, inclui descrições dos códigos
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.include_descriptions = include_descriptions

    def exportar(self, resultado: ResultadoProcessamento) -> str:
        """
        Exporta para string JSON.

        Args:
            resultado: Resultado do processamento

        Returns:
            String JSON formatada
        """
        dados = resultado.to_dict(include_descriptions=self.include_descriptions)
        return json.dumps(
            dados,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            cls=DecimalEncoder,
        )

    def exportar_arquivo(
            self,
            resultado: ResultadoProcessamento,
            caminho: Union[str, Path],
            encoding: str = "utf-8",
    ) -> None:
        """
        Exporta para arquivo JSON.

        Args:
            resultado: Resultado do processamento
            caminho: Caminho do arquivo de saída
            encoding: Encoding do arquivo
        """
        caminho = Path(caminho)
        json_str = self.exportar(resultado)
        caminho.write_text(json_str, encoding=encoding)

    def exportar_dict(self, resultado: ResultadoProcessamento) -> Dict[str, Any]:
        """
        Exporta para dicionário Python.

        Args:
            resultado: Resultado do processamento

        Returns:
            Dicionário com os dados
        """
        return resultado.to_dict(include_descriptions=self.include_descriptions)
