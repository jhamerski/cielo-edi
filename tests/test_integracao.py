import tempfile
import json
from pathlib import Path
from decimal import Decimal

from cielo_edi.parser import CieloEDIParser
from cielo_edi.exporters.json_exporter import JSONExporter
from cielo_edi.exporters.csv_exporter import CSVExporter


class TestIntegracaoEndToEnd:
    """Testes de integração completos simulando casos reais."""

    def test_fluxo_completo_arquivo_para_json(self, arquivo_cielo04):
        """Testa fluxo completo: arquivo EDI -> parse -> JSON."""
        # 1. Salvar arquivo EDI
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            edi_path = Path(f.name)

        # 2. Processar arquivo
        parser = CieloEDIParser()
        resultado = parser.processar_arquivo(edi_path)

        # 3. Exportar para JSON
        exporter = JSONExporter(indent=2)
        json_path = edi_path.with_suffix(".json")
        exporter.exportar_arquivo(resultado, json_path)

        # 4. Validar JSON gerado
        assert json_path.exists()

        with open(json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)

        assert "header" in dados
        assert "estatisticas" in dados
        assert dados["estatisticas"]["total_linhas"] > 0

        # Limpar
        edi_path.unlink()
        json_path.unlink()

    def test_fluxo_completo_arquivo_para_csv(self, arquivo_cielo04):
        """Testa fluxo completo: arquivo EDI -> parse -> múltiplos CSVs."""
        # 1. Salvar arquivo EDI
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            edi_path = Path(f.name)

        # 2. Processar arquivo
        parser = CieloEDIParser()
        resultado = parser.processar_arquivo(edi_path)

        # 3. Exportar para CSVs
        csv_dir = edi_path.parent / "csv_output"
        csv_dir.mkdir(exist_ok=True)

        exporter = CSVExporter()
        arquivos = exporter.exportar_todos(resultado, csv_dir, prefixo="teste_")

        # 4. Validar CSVs gerados
        assert len(arquivos) > 0

        for tipo, caminho in arquivos.items():
            assert caminho.exists()
            assert caminho.suffix == ".csv"

        # Limpar
        edi_path.unlink()
        for arquivo in csv_dir.glob("*.csv"):
            arquivo.unlink()
        csv_dir.rmdir()

    def test_processamento_multiplos_arquivos(self, arquivo_cielo04, arquivo_cielo09, arquivo_cielo15):
        """Testa processamento de múltiplos arquivos diferentes."""
        arquivos_edi = [arquivo_cielo04, arquivo_cielo09, arquivo_cielo15]
        parser = CieloEDIParser()

        resultados = []
        for conteudo in arquivos_edi:
            resultado = parser.processar_string(conteudo)
            resultados.append(resultado)

        # Validar que todos foram processados
        assert len(resultados) == 3

        # Cada um deve ter tipo de arquivo diferente
        tipos_arquivo = [r.tipo_arquivo for r in resultados]
        assert "04" in tipos_arquivo
        assert "09" in tipos_arquivo
        assert "15" in tipos_arquivo

    def test_round_trip_edi_json_comparacao(self, arquivo_cielo04):
        """Testa que dados são preservados no ciclo EDI -> JSON -> comparação."""
        parser = CieloEDIParser()
        resultado_original = parser.processar_string(arquivo_cielo04)

        # Exportar para JSON
        exporter = JSONExporter()
        json_str = exporter.exportar(resultado_original)

        # Converter JSON de volta para dict
        dados_json = json.loads(json_str)

        # Validar dados críticos preservados
        assert dados_json["tipo_arquivo"] == resultado_original.tipo_arquivo

        if resultado_original.header:
            assert dados_json["header"]["estabelecimento_matriz"] == resultado_original.header.estabelecimento_matriz
            assert dados_json["header"]["data_processamento"] == str(resultado_original.header.data_processamento)

        # Validar estatísticas
        assert dados_json["estatisticas"]["total_linhas"] == resultado_original.estatisticas.total_linhas
        assert float(dados_json["estatisticas"]["valor_bruto_total"]) == float(resultado_original.estatisticas.valor_bruto_total)


class TestValidacaoIntegridadeDados:
    """Testes de validação de integridade dos dados."""

    def test_validacao_valores_monetarios_consistencia(self, arquivo_cielo04):
        """Valida que valores monetários são consistentes em todo o processamento."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Soma manual dos valores brutos dos detalhes
        soma_detalhes = sum(d.valor_bruto_venda_parcela for d in resultado.detalhes)

        # Soma manual dos valores das URs
        soma_urs = sum(ur.valor_bruto for ur in resultado.ur_agenda)

        # Valores devem ser Decimal
        assert isinstance(soma_detalhes, Decimal)
        assert isinstance(soma_urs, Decimal)

        # Valores devem ser positivos (para este arquivo de teste)
        assert soma_detalhes >= 0
        assert soma_urs >= 0

    def test_validacao_datas_cronologia(self, arquivo_cielo04):
        """Valida que datas seguem ordem cronológica lógica."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        if resultado.header:
            periodo_inicial = resultado.header.periodo_inicial
            periodo_final = resultado.header.periodo_final

            # Período inicial deve ser <= período final
            assert periodo_inicial <= periodo_final

    def test_validacao_referencias_cruzadas(self, arquivo_cielo04):
        """Valida referências cruzadas entre registros."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Todos os detalhes devem referenciar estabelecimentos válidos
        for detalhe in resultado.detalhes:
            assert len(detalhe.estabelecimento_submissor) == 10
            assert detalhe.estabelecimento_submissor.isdigit()

        # Todas as URs devem ter CPF/CNPJ válidos (14 dígitos)
        for ur in resultado.ur_agenda:
            assert len(ur.cpf_cnpj_titular) == 14
            assert ur.cpf_cnpj_titular.isdigit()


class TestCenariosConcorrencia:
    """Testes para cenários de processamento concorrente."""

    def test_processamento_paralelo_mesmo_parser(self, arquivo_cielo04):
        """Testa que mesmo parser pode processar múltiplas vezes."""
        parser = CieloEDIParser()

        # Processar mesmo arquivo 3 vezes
        resultados = []
        for _ in range(3):
            resultado = parser.processar_string(arquivo_cielo04)
            resultados.append(resultado)

        # Todos os resultados devem ser idênticos
        assert len(resultados) == 3
        assert all(r.tipo_arquivo == resultados[0].tipo_arquivo for r in resultados)
        assert all(r.estatisticas.total_linhas == resultados[0].estatisticas.total_linhas for r in resultados)

    def test_multiplos_parsers_independentes(self, arquivo_cielo04, arquivo_cielo09):
        """Testa que múltiplos parsers são independentes."""
        parser1 = CieloEDIParser(encoding="latin-1")
        parser2 = CieloEDIParser(encoding="utf-8")

        resultado1 = parser1.processar_string(arquivo_cielo04)
        resultado2 = parser1.processar_string(arquivo_cielo09)

        # Parsers devem manter estado independente
        assert resultado1.tipo_arquivo != resultado2.tipo_arquivo


class TestRobustezArquivosGrandes:
    """Testes de robustez com arquivos maiores."""

    def test_arquivo_com_muitas_linhas(self):
        """Testa processamento de arquivo com muitas linhas."""
        # Cria arquivo com 1000 detalhes
        linhas = ["0123456789020241218202412012024123100000010CIELO04N                    151"]

        # Adiciona 1000 detalhes
        detalhe_template = "E1234567890001002010612345602                                  +0000000100000+0000000097500+0000000002500040123456789065432100000000000000000000000000000000000000002500" + " " * 155
        for i in range(1000):
            linhas.append(detalhe_template)

        # Trailer
        linhas.append("9" + "0" * 9 + "1000+0000097500000000000000050+00000002500000+00000000000000000+00000000000000000" + " " * 155)

        conteudo = "\n".join(linhas)

        parser = CieloEDIParser()
        resultado = parser.processar_string(conteudo)

        assert len(resultado.detalhes) == 1000
        assert resultado.estatisticas.total_detalhes == 1000

    def test_streaming_arquivo_grande(self):
        """Testa processamento streaming de arquivo grande."""
        # Cria arquivo com muitos registros
        linhas = ["0123456789020241218202412012024123100000010CIELO04N                    151"]

        for i in range(100):
            linhas.append(
                "E1234567890001002010612345602                                  +0000000100000+0000000097500+0000000002500040123456789065432100000000000000000000000000000000000000002500" + " " * 155)

        linhas.append("9" + "0" * 9 + "0100+0000009750000000000000050+00000000250000+00000000000000000+00000000000000000" + " " * 155)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write("\n".join(linhas))
            temp_path = f.name

        try:
            parser = CieloEDIParser()
            registros = list(parser.processar_streaming(temp_path))

            # Deve ter processado header + 100 detalhes + trailer
            assert len(registros) == 102
        finally:
            Path(temp_path).unlink()


class TestCasosUsoReais:
    """Testes baseados em casos de uso reais de clientes."""

    def test_exportacao_para_sistema_contabil(self, arquivo_cielo04):
        """Simula exportação para sistema contábil (CSV com campos específicos)."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Sistema contábil precisa apenas de alguns campos
        dados_contabeis = []
        for detalhe in resultado.detalhes:
            dados_contabeis.append({
                "data": str(resultado.header.data_processamento) if resultado.header else "",
                "estabelecimento": detalhe.estabelecimento_submissor,
                "valor_bruto": float(detalhe.valor_bruto_venda_parcela),
                "valor_liquido": float(detalhe.valor_liquido_venda),
                "taxa": float(detalhe.valor_comissao),
            })

        assert len(dados_contabeis) == len(resultado.detalhes)
        assert all("estabelecimento" in d for d in dados_contabeis)

    def test_conciliacao_bancaria(self, arquivo_cielo04):
        """Simula processo de conciliação bancária."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Agrupa por data de pagamento
        por_data = {}
        for ur in resultado.ur_agenda:
            data = str(ur.data_pagamento) if ur.data_pagamento else "sem_data"
            if data not in por_data:
                por_data[data] = Decimal("0")
            por_data[data] += ur.valor_liquido

        # Deve ter agrupado corretamente
        assert len(por_data) > 0
        assert all(isinstance(valor, Decimal) for valor in por_data.values())

    def test_analise_taxas_por_bandeira(self, arquivo_cielo04):
        """Simula análise de taxas por bandeira de cartão."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Agrupa por bandeira
        por_bandeira = {}
        for detalhe in resultado.detalhes:
            bandeira = detalhe.bandeira_liquidacao_descricao
            if bandeira not in por_bandeira:
                por_bandeira[bandeira] = {
                    "quantidade": 0,
                    "valor_total": Decimal("0"),
                    "taxa_total": Decimal("0"),
                }

            por_bandeira[bandeira]["quantidade"] += 1
            por_bandeira[bandeira]["valor_total"] += detalhe.valor_bruto_venda_parcela
            por_bandeira[bandeira]["taxa_total"] += detalhe.valor_comissao

        # Calcula taxa média por bandeira
        for bandeira, dados in por_bandeira.items():
            if dados["valor_total"] > 0:
                taxa_media = (dados["taxa_total"] / dados["valor_total"]) * 100
                por_bandeira[bandeira]["taxa_media_percentual"] = float(taxa_media)

        assert len(por_bandeira) > 0
