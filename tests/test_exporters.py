import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from cielo_edi.parser import CieloEDIParser
from cielo_edi.exporters.json_exporter import JSONExporter, DecimalEncoder
from cielo_edi.exporters.csv_exporter import CSVExporter


class TestDecimalEncoder:
    """Testes para o encoder JSON customizado."""

    def test_encode_decimal(self):
        """Testa encoding de Decimal."""
        data = {"valor": Decimal("123.45")}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"valor": 123.45}'

    def test_encode_date(self):
        """Testa encoding de date."""
        from datetime import date
        data = {"data": date(2024, 12, 18)}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"data": "2024-12-18"}'

    def test_encode_time(self):
        """Testa encoding de time."""
        from datetime import time
        data = {"hora": time(14, 30, 25)}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"hora": "14:30:25"}'


class TestJSONExporter:
    """Testes para o exportador JSON."""

    def test_exportar_string(self, arquivo_edi_completo):
        """Testa exportação para string JSON."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        exporter = JSONExporter(indent=2)
        json_str = exporter.exportar(resultado)

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert "header" in data
        assert "detalhes" in data
        assert "estatisticas" in data

    def test_exportar_minificado(self, arquivo_edi_completo):
        """Testa exportação minificada."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        exporter = JSONExporter(indent=None)
        json_str = exporter.exportar(resultado)

        # JSON minificado não tem newlines
        assert "\n" not in json_str

    def test_exportar_arquivo(self, arquivo_edi_completo):
        """Testa exportação para arquivo."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            exporter = JSONExporter()
            exporter.exportar_arquivo(resultado, temp_path)

            assert temp_path.exists()
            content = temp_path.read_text(encoding="utf-8")
            data = json.loads(content)
            assert "header" in data
        finally:
            temp_path.unlink()

    def test_exportar_dict(self, arquivo_edi_completo):
        """Testa exportação para dicionário."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        exporter = JSONExporter()
        data = exporter.exportar_dict(resultado)

        assert isinstance(data, dict)
        assert data["tipo_arquivo"] == "04"


class TestCSVExporter:
    """Testes para o exportador CSV."""

    def test_exportar_detalhes(self, arquivo_edi_completo):
        """Testa exportação de detalhes para CSV."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        exporter = CSVExporter()
        csv_str = exporter.exportar(resultado, "detalhes")

        assert isinstance(csv_str, str)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # header + 1 linha
        assert "tipo_registro" in lines[0]

    def test_exportar_ur_agenda(self, arquivo_edi_completo):
        """Testa exportação de UR agenda para CSV."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        exporter = CSVExporter()
        csv_str = exporter.exportar(resultado, "ur_agenda")

        lines = csv_str.strip().split("\n")
        assert len(lines) == 2

    def test_exportar_vazio(self, arquivo_edi_minimo):
        """Testa exportação de lista vazia."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_minimo)

        exporter = CSVExporter()
        csv_str = exporter.exportar(resultado, "pix")

        assert csv_str == ""

    def test_exportar_arquivo(self, arquivo_edi_completo):
        """Testa exportação para arquivo CSV."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            exporter = CSVExporter()
            exporter.exportar_arquivo(resultado, "detalhes", temp_path)

            assert temp_path.exists()
            content = temp_path.read_text(encoding="utf-8-sig")
            assert "tipo_registro" in content
        finally:
            temp_path.unlink()

    def test_exportar_todos(self, arquivo_edi_completo):
        """Testa exportação de todos os tipos para diretório."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter()
            arquivos = exporter.exportar_todos(resultado, temp_dir, prefixo="teste_")

            # Deve criar arquivos para ur_agenda e detalhes
            assert "ur_agenda" in arquivos
            assert "detalhes" in arquivos

            for tipo, caminho in arquivos.items():
                assert caminho.exists()
                assert caminho.name.startswith("teste_")

    def test_delimiter_customizado(self, arquivo_edi_completo):
        """Testa uso de delimiter customizado."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        exporter = CSVExporter(delimiter=",")
        csv_str = exporter.exportar(resultado, "detalhes")

        # Verifica se usa vírgula como delimiter
        lines = csv_str.strip().split("\n")
        assert "," in lines[0]


class TestCSVExporterConversores:
    """Testes para conversores de valores do CSVExporter."""

    def test_converter_valor_decimal(self, arquivo_cielo04):
        """Testa conversão de Decimal para string CSV."""
        from cielo_edi.parser import CieloEDIParser

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        exporter = CSVExporter()
        csv_str = exporter.exportar(resultado, "ur_agenda")

        # Verifica que valores Decimal foram convertidos
        assert csv_str is not None
        assert "1000" in csv_str or "975" in csv_str

    def test_converter_valor_bool(self):
        """Testa conversão de booleano para string CSV."""
        exporter = CSVExporter()

        # Testa conversão direta do método interno
        assert exporter._converter_valor(True) == "1"
        assert exporter._converter_valor(False) == "0"


class TestJSONExporterEncoder:
    """Testes para o encoder JSON customizado."""

    def test_decimal_encoder_objeto_nao_serializavel(self):
        """Testa encoder com objeto não serializável."""
        encoder = DecimalEncoder()

        # Testa com objeto não suportado - deve chamar super().default()
        class ObjetoCustomizado:
            pass

        obj = ObjetoCustomizado()

        with pytest.raises(TypeError):
            encoder.default(obj)


class TestJSONExporterCobertura:
    """Testes adicionais para JSONExporter."""

    def test_exportar_dict_com_encoding_especifico(self, arquivo_cielo04):
        """Testa exportar_dict com encoding específico."""
        from cielo_edi.parser import CieloEDIParser

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        exporter = JSONExporter(indent=2)
        dict_resultado = exporter.exportar_dict(resultado)

        # Verifica que é um dicionário válido
        assert isinstance(dict_resultado, dict)
        assert "header" in dict_resultado
        assert "estatisticas" in dict_resultado


class TestCSVExporterCobertura:
    """Testes adicionais para CSVExporter."""

    def test_exportar_arquivo_sem_dados(self, tmpdir):
        """Testa exportar arquivo CSV sem registros."""
        from cielo_edi.models import ResultadoProcessamento

        resultado = ResultadoProcessamento()
        exporter = CSVExporter()

        csv_file = Path(tmpdir) / "detalhes.csv"
        exporter.exportar_arquivo(resultado, "detalhes", csv_file)

        # Verifica que arquivo foi criado
        assert csv_file.exists()

    def test_exportar_com_delimiter_customizado(self, arquivo_cielo04, tmpdir):
        """Testa exportar com delimitador customizado."""
        from cielo_edi.parser import CieloEDIParser

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        exporter = CSVExporter(delimiter=";")
        csv_file = Path(tmpdir) / "detalhes.csv"

        exporter.exportar_arquivo(resultado, "detalhes", csv_file)

        assert csv_file.exists()
        conteudo = csv_file.read_text(encoding="utf-8")
        assert ";" in conteudo  # Verifica delimitador
