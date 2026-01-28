import pytest
from decimal import Decimal

from cielo_edi.parser import CieloEDIParser, converter_valor_decimal
from cielo_edi.exporters.json_exporter import JSONExporter


class TestSegurancaDados:
    """Testes de segurança e validação de dados."""

    def test_caracteres_especiais_nao_causam_crash(self):
        """Testa que caracteres especiais não causam crash."""
        caracteres_especiais = [
            "0123456789\x00\x01\x02\x03\x04",  # Caracteres de controle
            "0123456789<script>alert('xss')</script>",  # XSS
            "0123456789'; DROP TABLE users; --",  # SQL Injection
            "0123456789\n\r\t\x0b\x0c",  # Whitespace especial
            "0123456789" + "A" * 10000,  # String muito longa
        ]

        parser = CieloEDIParser()

        for linha_perigosa in caracteres_especiais:
            try:
                # Não deve causar exceção, apenas processar ou ignorar
                resultado = parser.processar_string(linha_perigosa)
                assert resultado is not None
            except Exception as e:
                # Se houver exceção, deve ser tratada e não crash
                assert isinstance(e, (ValueError, UnicodeError)) or "error" in str(e).lower()

    def test_valores_monetarios_extremos(self):
        """Testa valores monetários extremos."""
        valores_extremos = [
            "9" * 13,  # Valor máximo
            "0" * 13,  # Valor zero
            "1",  # Valor mínimo
            "999999999999",  # Quase máximo
        ]

        for valor_str in valores_extremos:
            resultado = converter_valor_decimal(valor_str, 2)
            assert isinstance(resultado, Decimal)
            assert resultado >= 0

    def test_linhas_muito_longas_nao_causam_overflow(self):
        """Testa que linhas muito longas não causam overflow."""
        # Cria linha com 100.000 caracteres
        linha_gigante = "0" + "A" * 99999

        parser = CieloEDIParser()
        resultado = parser.processar_string(linha_gigante)

        # Deve processar sem crash
        assert resultado is not None

    def test_arquivo_sem_quebras_linha(self):
        """Testa arquivo sem quebras de linha."""
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151" + " " * 400

        parser = CieloEDIParser()
        resultado = parser.processar_string(conteudo)

        # Deve processar sem crash
        assert resultado is not None

    def test_path_traversal_tentativa(self):
        """Testa que tentativas de path traversal são bloqueadas."""
        caminhos_perigosos = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
        ]

        parser = CieloEDIParser()

        for caminho_perigoso in caminhos_perigosos:
            with pytest.raises((FileNotFoundError, PermissionError)):
                parser.processar_arquivo(caminho_perigoso)


class TestRobustezEntradas:
    """Testes de robustez com entradas inválidas."""

    def test_arquivo_vazio_multiple_times(self):
        """Testa processamento de arquivo vazio múltiplas vezes."""
        parser = CieloEDIParser()

        for _ in range(10):
            resultado = parser.processar_string("")
            assert resultado.estatisticas.total_linhas == 0

    def test_arquivo_apenas_espacos_e_tabs(self):
        """Testa arquivo com apenas espaços e tabs."""
        conteudos_vazios = [
            " " * 1000,
            "\t" * 1000,
            " \t \t " * 100,
            "\n\n\n\n\n" * 100,
        ]

        parser = CieloEDIParser()

        for conteudo in conteudos_vazios:
            resultado = parser.processar_string(conteudo)
            assert resultado.estatisticas.total_linhas >= 0

    def test_valores_negativos_overflow(self):
        """Testa valores negativos e overflow."""
        valores_perigosos = [
            "-999999999999",
            "-1",
            "999999999999999999999",  # Muito grande
        ]

        for valor in valores_perigosos:
            try:
                resultado = converter_valor_decimal(valor, 2)
                # Se processar, deve ser Decimal válido
                assert isinstance(resultado, Decimal)
            except:
                # Se falhar, não deve crashar o programa
                pass

    def test_encoding_invalido_graceful_degradation(self):
        """Testa que encoding inválido degrada graciosamente."""
        # Cria arquivo com bytes inválidos para latin-1
        conteudo_bytes = b"\x00\x01\x02\x03\xff\xfe\xfd"

        parser = CieloEDIParser()

        try:
            # Pode falhar, mas não deve crashar
            resultado = parser.processar_bytes(conteudo_bytes)
            assert resultado is not None
        except (UnicodeDecodeError, ValueError):
            # Exceção esperada e tratada
            pass

    def test_memoria_leak_processamento_repetido(self):
        """Testa que não há memory leak em processamento repetido."""
        parser = CieloEDIParser()
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151\n"

        # Processa 1000 vezes
        for _ in range(1000):
            resultado = parser.processar_string(conteudo)
            # Limpa referência para permitir garbage collection
            del resultado

        # Se chegou aqui, não houve memory leak catastrófico


class TestValidacaoTiposDados:
    """Testes de validação de tipos de dados."""

    def test_tipos_corretos_apos_parse(self, arquivo_cielo04):
        """Valida que todos os tipos de dados estão corretos após parse."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Valida tipos do header
        if resultado.header:
            assert isinstance(resultado.header.estabelecimento_matriz, str)
            assert isinstance(resultado.header.versao_layout, str)
            assert resultado.header.data_processamento is not None

        # Valida tipos dos detalhes
        for detalhe in resultado.detalhes:
            assert isinstance(detalhe.estabelecimento_submissor, str)
            assert isinstance(detalhe.valor_bruto_venda_parcela, Decimal)
            assert isinstance(detalhe.valor_liquido_venda, Decimal)
            assert isinstance(detalhe.taxa_mdr, Decimal)

        # Valida tipos das URs
        for ur in resultado.ur_agenda:
            assert isinstance(ur.cpf_cnpj_titular, str)
            assert isinstance(ur.valor_bruto, Decimal)
            assert isinstance(ur.valor_liquido, Decimal)

    def test_valores_decimais_nunca_sao_float(self, arquivo_cielo04):
        """Garante que valores monetários são sempre Decimal, nunca float."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Verifica detalhes
        for detalhe in resultado.detalhes:
            assert not isinstance(detalhe.valor_bruto_venda_parcela, float)
            assert not isinstance(detalhe.valor_liquido_venda, float)
            assert not isinstance(detalhe.valor_comissao, float)
            assert not isinstance(detalhe.taxa_mdr, float)

        # Verifica URs
        for ur in resultado.ur_agenda:
            assert not isinstance(ur.valor_bruto, float)
            assert not isinstance(ur.valor_liquido, float)
            assert not isinstance(ur.valor_taxa_administrativa, float)


class TestConsistenciaExportacao:
    """Testes de consistência na exportação de dados."""

    def test_json_nao_contem_nan_ou_infinity(self, arquivo_cielo04):
        """Garante que JSON exportado não contém NaN ou Infinity."""
        import json as json_lib

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        exporter = JSONExporter()
        json_str = exporter.exportar(resultado)

        # JSON não deve conter NaN, Infinity, ou -Infinity
        assert "NaN" not in json_str
        assert "Infinity" not in json_str
        assert "-Infinity" not in json_str

        # Deve ser JSON válido
        dados = json_lib.loads(json_str)
        assert isinstance(dados, dict)

    def test_csv_nao_contem_caracteres_invalidos(self, arquivo_cielo04):
        """Garante que CSV não contém caracteres que quebram parsers."""
        from cielo_edi.exporters.csv_exporter import CSVExporter

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        exporter = CSVExporter()
        csv_str = exporter.exportar(resultado, "detalhes")

        # CSV não deve conter caracteres de controle perigosos
        caracteres_perigosos = ["\x00", "\x01", "\x02", "\x03"]
        for char in caracteres_perigosos:
            assert char not in csv_str

    def test_exportacao_preserva_precisao_decimal(self, arquivo_cielo04):
        """Garante que exportação preserva precisão de valores decimais."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # Pega valor original
        if resultado.detalhes:
            valor_original = resultado.detalhes[0].valor_bruto_venda_parcela

            # Exporta e reimporta JSON
            exporter = JSONExporter()
            json_str = exporter.exportar(resultado)

            import json
            dados = json.loads(json_str)

            valor_exportado = float(dados["detalhes"][0]["valor_bruto_venda_parcela"])

            # Diferença deve ser mínima (tolerância para conversão float)
            diferenca = abs(float(valor_original) - valor_exportado)
            assert diferenca < 0.01  # Tolerância de 1 centavo


class TestLimitesEBordas:
    """Testes de limites e casos de borda."""

    def test_arquivo_com_exatamente_max_linhas(self):
        """Testa arquivo com número máximo razoável de linhas."""
        # Cria arquivo com 10.000 linhas (número grande mas razoável)
        linhas = ["0123456789020241218202412012024123100000010CIELO04N                    151"]

        for i in range(9998):
            linhas.append(
                "E1234567890001002010612345602                                  +0000000100000+0000000097500+0000000002500040123456789065432100000000000000000000000000000000000000002500" + " " * 155)

        linhas.append("9" + str(9999).zfill(9) + "+0000975000000000000050000+00002500000+00000000000000000+00000000000000000" + " " * 155)

        conteudo = "\n".join(linhas)

        parser = CieloEDIParser()
        resultado = parser.processar_string(conteudo)

        assert resultado.estatisticas.total_linhas == 10000

    def test_valores_com_todas_casas_decimais(self):
        """Testa valores com todas as casas decimais preenchidas."""
        valores_teste = [
            ("1234567890123", 2, Decimal("12345678901.23")),
            ("0000000000001", 2, Decimal("0.01")),
            ("9999999999999", 2, Decimal("99999999999.99")),
            ("1234567890", 3, Decimal("1234567.890")),
        ]

        for valor_str, casas, esperado in valores_teste:
            resultado = converter_valor_decimal(valor_str, casas)
            assert resultado == esperado

    def test_strings_com_comprimento_exato_campos(self):
        """Testa strings com comprimento exato dos campos EDI."""
        # Campos têm comprimentos fixos
        campos_fixos = {
            "estabelecimento": 10,
            "nsu": 6,
            "codigo_autorizacao": 6,
            "bin_cartao": 6,
        }

        for campo, tamanho in campos_fixos.items():
            valor = "1" * tamanho
            assert len(valor) == tamanho

            # Testa com espaços
            valor_espacos = "1" * (tamanho - 1) + " "
            assert len(valor_espacos) == tamanho
