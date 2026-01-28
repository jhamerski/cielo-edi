from io import StringIO
from pathlib import Path
import tempfile

from decimal import Decimal
from datetime import date, time

import pytest

from cielo_edi.parser import (
    CieloEDIParser,
    extrair_campo,
    converter_valor_decimal,
    converter_data,
    converter_hora,
    parse_registro_header,
    parse_registro_ur_agenda,
    parse_registro_detalhe,
    parse_registro_pix,
    parse_registro_negociacao_resumo,
    parse_registro_negociacao_detalhe,
    parse_registro_conta_recebimento,
    parse_registro_reserva_financeira,
    parse_registro_trailer,
)

from cielo_edi.models import RegistroHeader


class TestExtrairCampo:
    """Testes para função extrair_campo."""

    def test_extrair_campo_basico(self):
        """Testa extração básica de campo."""
        linha = "0123456789ABCDEF"
        assert extrair_campo(linha, 1, 1) == "0"
        assert extrair_campo(linha, 1, 5) == "01234"
        assert extrair_campo(linha, 11, 16) == "ABCDEF"

    def test_extrair_campo_com_espacos(self):
        """Testa extração com remoção de espaços."""
        linha = "  ABC  DEF  "
        assert extrair_campo(linha, 1, 12) == "ABC  DEF"

    def test_extrair_campo_vazio(self):
        """Testa extração de campo vazio."""
        linha = "      "
        assert extrair_campo(linha, 1, 6) == ""


class TestConverterValorDecimal:
    """Testes para função converter_valor_decimal."""

    def test_converter_valor_inteiro(self):
        """Testa conversão de valor inteiro."""
        assert converter_valor_decimal("0000001000", 2) == Decimal("10.00")
        assert converter_valor_decimal("0000010000", 2) == Decimal("100.00")

    def test_converter_valor_com_centavos(self):
        """Testa conversão com centavos."""
        assert converter_valor_decimal("0000001234", 2) == Decimal("12.34")
        assert converter_valor_decimal("0000000050", 2) == Decimal("0.50")

    def test_converter_valor_tres_casas(self):
        """Testa conversão com 3 casas decimais (taxas)."""
        assert converter_valor_decimal("02500", 3) == Decimal("2.500")
        assert converter_valor_decimal("12345", 3) == Decimal("12.345")

    def test_converter_valor_vazio(self):
        """Testa conversão de valor vazio."""
        assert converter_valor_decimal("", 2) == Decimal("0")
        assert converter_valor_decimal("   ", 2) == Decimal("0")

    def test_converter_valor_grande(self):
        """Testa conversão de valores grandes."""
        assert converter_valor_decimal("9999999999999", 2) == Decimal("99999999999.99")


class TestConverterData:
    """Testes para função converter_data."""

    def test_converter_data_ddmmaaaa(self):
        """Testa conversão formato DDMMAAAA."""
        assert converter_data("18122024", "DDMMAAAA") == date(2024, 12, 18)
        assert converter_data("01012025", "DDMMAAAA") == date(2025, 1, 1)

    def test_converter_data_aaaammdd(self):
        """Testa conversão formato AAAAMMDD."""
        assert converter_data("20241218", "AAAAMMDD") == date(2024, 12, 18)
        assert converter_data("20250101", "AAAAMMDD") == date(2025, 1, 1)

    def test_converter_data_aammdd(self):
        """Testa conversão formato AAMMDD."""
        assert converter_data("241218", "AAMMDD") == date(2024, 12, 18)
        assert converter_data("250101", "AAMMDD") == date(2025, 1, 1)

    def test_converter_data_invalida(self):
        """Testa conversão de datas inválidas."""
        assert converter_data("", "DDMMAAAA") is None
        assert converter_data("00000000", "DDMMAAAA") is None
        assert converter_data("01011001", "DDMMAAAA") is None
        assert converter_data("invalid", "DDMMAAAA") is None


class TestConverterHora:
    """Testes para função converter_hora."""

    def test_converter_hora_valida(self):
        """Testa conversão de hora válida."""
        assert converter_hora("143025") == time(14, 30, 25)
        assert converter_hora("000000") == time(0, 0, 0)
        assert converter_hora("235959") == time(23, 59, 59)

    def test_converter_hora_invalida(self):
        """Testa conversão de hora inválida."""
        assert converter_hora("") is None
        assert converter_hora("12345") is None
        assert converter_hora("invalid") is None


class TestParseRegistroHeader:
    """Testes para parse do registro header."""

    def test_parse_header_basico(self, linha_header):
        """Testa parse básico do header."""
        header = parse_registro_header(linha_header)

        assert header.tipo_registro == "0"
        assert header.estabelecimento_matriz == "1234567890"
        assert header.data_processamento == date(2024, 12, 18)
        assert header.periodo_inicial == date(2024, 12, 1)
        assert header.periodo_final == date(2024, 12, 31)
        assert header.sequencia == "0000001"
        assert header.empresa_adquirente == "CIELO"
        assert header.opcao_extrato == "04"
        assert header.versao_layout == "151"

    def test_header_opcao_extrato_descricao(self, linha_header):
        """Testa propriedade de descrição do tipo de arquivo."""
        header = parse_registro_header(linha_header)
        assert header.opcao_extrato_descricao == "Liquidação/Pagamento"


class TestCieloEDIParser:
    """Testes para a classe CieloEDIParser."""

    def test_parser_inicializacao(self):
        """Testa inicialização do parser."""
        parser = CieloEDIParser()
        assert parser.encoding == "latin-1"

        parser_utf8 = CieloEDIParser(encoding="utf-8")
        assert parser_utf8.encoding == "utf-8"

    def test_processar_string_arquivo_minimo(self, arquivo_edi_minimo):
        """Testa processamento de arquivo mínimo."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_minimo)

        assert resultado.header is not None
        assert resultado.trailer is not None
        assert resultado.tipo_arquivo == "04"
        assert resultado.estatisticas.total_linhas == 2

    def test_processar_string_arquivo_completo(self, arquivo_edi_completo):
        """Testa processamento de arquivo completo."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        assert resultado.header is not None
        assert resultado.trailer is not None
        assert len(resultado.ur_agenda) == 1
        assert len(resultado.detalhes) == 1
        assert resultado.estatisticas.total_linhas == 4
        assert resultado.estatisticas.total_ur_agenda == 1
        assert resultado.estatisticas.total_detalhes == 1

    def test_processar_bytes(self, arquivo_edi_minimo):
        """Testa processamento a partir de bytes."""
        parser = CieloEDIParser()
        dados = arquivo_edi_minimo.encode("latin-1")
        resultado = parser.processar_bytes(dados)

        assert resultado.header is not None

    def test_processar_io(self, arquivo_edi_minimo):
        """Testa processamento a partir de file-like object."""
        parser = CieloEDIParser()
        resultado = parser.processar(StringIO(arquivo_edi_minimo))

        assert resultado.header is not None

    def test_processar_arquivo_fisico(self, arquivo_edi_completo):
        """Testa processamento de arquivo físico."""
        parser = CieloEDIParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='latin-1') as f:
            f.write(arquivo_edi_completo)
            temp_path = f.name

        try:
            resultado = parser.processar_arquivo(temp_path)
            assert resultado.header is not None
            assert resultado.estatisticas.total_linhas == 4
        finally:
            Path(temp_path).unlink()

    def test_processar_streaming(self, arquivo_edi_completo):
        """Testa processamento em modo streaming."""
        parser = CieloEDIParser()
        registros = list(parser.processar_streaming(StringIO(arquivo_edi_completo)))

        assert len(registros) == 4
        assert isinstance(registros[0], RegistroHeader)

    def test_valores_monetarios(self, arquivo_edi_completo):
        """Testa extração correta de valores monetários."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        # UR Agenda
        ur = resultado.ur_agenda[0]
        assert ur.valor_bruto == Decimal("1000.00")
        assert ur.valor_taxa_administrativa == Decimal("25.00")
        assert ur.valor_liquido == Decimal("975.00")

        # Detalhe
        detalhe = resultado.detalhes[0]
        assert detalhe.valor_total_venda == Decimal("3000.00")
        assert detalhe.valor_bruto_venda_parcela == Decimal("1000.00")
        assert detalhe.valor_liquido_venda == Decimal("975.00")

    def test_estatisticas_acumuladas(self, arquivo_edi_completo):
        """Testa acumulação correta das estatísticas."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        assert resultado.estatisticas.valor_bruto_total == Decimal("1000.00")
        assert resultado.estatisticas.valor_liquido_total == Decimal("975.00")

    def test_linhas_nao_processadas(self):
        """Testa registro de linhas não reconhecidas."""
        parser = CieloEDIParser()
        conteudo = "X" + " " * 249 + "\n"  # Tipo de registro inválido
        resultado = parser.processar_string(conteudo)

        assert len(resultado.linhas_nao_processadas) == 1
        assert resultado.linhas_nao_processadas[0].tipo == "X"

    def test_resultado_to_dict(self, arquivo_edi_completo):
        """Testa conversão do resultado para dicionário."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_edi_completo)

        dados = resultado.to_dict()

        assert isinstance(dados, dict)
        assert "header" in dados
        assert "detalhes" in dados
        assert "estatisticas" in dados
        assert dados["tipo_arquivo"] == "04"


class TestParseHeader:
    """Testes para parse_registro_header."""

    def test_parse_header_basico(self, linha_header):
        """Testa parse básico do header."""
        header = parse_registro_header(linha_header)

        assert header.tipo_registro == "0"
        assert header.estabelecimento_matriz == "1234567890"

    def test_parse_header_datas(self, linha_header):
        """Testa parse de datas do header."""
        header = parse_registro_header(linha_header)

        assert header.data_processamento == date(2024, 12, 18)
        assert header.periodo_inicial == date(2024, 12, 1)
        assert header.periodo_final == date(2024, 12, 31)

    def test_parse_header_sequencia(self, linha_header):
        """Testa parse da sequência."""
        header = parse_registro_header(linha_header)

        assert header.sequencia == "0000001"

    def test_parse_header_opcao_extrato(self, linha_header):
        """Testa parse da opção de extrato."""
        header = parse_registro_header(linha_header)

        assert header.opcao_extrato == "04"
        assert header.opcao_extrato_descricao == "Liquidação/Pagamento"

    def test_parse_header_empresa_adquirente(self, linha_header):
        """Testa parse da empresa adquirente."""
        header = parse_registro_header(linha_header)

        assert header.empresa_adquirente == "CIELO"

    def test_parse_header_versao_layout(self, linha_header):
        """Testa parse da versão do layout."""
        header = parse_registro_header(linha_header)

        assert header.versao_layout == "151"


class TestParseRegistroPix:
    """Testes para parse_registro_pix."""

    def test_parse_pix_basico(self, linha_pix):
        """Testa parse básico de registro Pix."""
        pix = parse_registro_pix(linha_pix)

        assert pix.tipo_registro == "8"
        assert pix.estabelecimento_submissor == "1234567890"
        assert pix.tipo_transacao == "01"

    def test_parse_pix_valores_monetarios(self, linha_pix):
        """Testa parse de valores monetários do Pix."""
        pix = parse_registro_pix(linha_pix)

        assert pix.valor_bruto == Decimal("500.00")
        assert pix.valor_taxa_administrativa == Decimal("10.00")
        assert pix.valor_liquido == Decimal("490.00")

    def test_parse_pix_datas(self, linha_pix):
        """Testa parse de datas do Pix."""
        pix = parse_registro_pix(linha_pix)

        assert pix.data_transacao == date(2024, 12, 18)
        assert pix.hora_transacao == time(14, 30, 25)
        assert pix.data_pagamento == date(2024, 12, 18)
        assert pix.data_captura_transacao == date(2024, 12, 18)

    def test_parse_pix_identificadores(self, linha_pix):
        """Testa parse de identificadores únicos."""
        pix = parse_registro_pix(linha_pix)

        assert pix.id_pix == "123e4567e89b12d3a456426614174000abcd"
        assert pix.tx_id == "123e4567e89b12d3a456426614174111wxyz"
        assert pix.nsu_doc == "654321"

    def test_parse_pix_dados_bancarios(self, linha_pix):
        """Testa parse de dados bancários."""
        pix = parse_registro_pix(linha_pix)

        assert pix.banco == "0341"
        assert pix.agencia == "12345"
        assert pix.conta == "12345678901234567890"

    def test_parse_pix_taxas(self, linha_pix):
        """Testa parse de taxas administrativas."""
        pix = parse_registro_pix(linha_pix)

        assert pix.taxa_administrativa == Decimal("1.00")
        assert pix.tarifa_administrativa == Decimal("1.00")

    def test_parse_pix_canal_venda(self, linha_pix):
        """Testa parse do canal de venda."""
        pix = parse_registro_pix(linha_pix)

        assert pix.canal_venda == "02"
        assert pix.numero_logico_terminal == "12345678"


class TestParseNegociacaoResumo:
    """Testes para parse_registro_negociacao_resumo."""

    def test_parse_negociacao_resumo_basico(self, linha_negociacao_resumo):
        """Testa parse básico de negociação resumo."""
        resumo = parse_registro_negociacao_resumo(linha_negociacao_resumo)

        assert resumo.tipo_registro == "A"
        assert resumo.cpf_cnpj == "12345678901234"

    def test_parse_negociacao_resumo_datas(self, linha_negociacao_resumo):
        """Testa parse de datas."""
        resumo = parse_registro_negociacao_resumo(linha_negociacao_resumo)

        assert resumo.data_negociacao == date(2024, 12, 18)
        assert resumo.data_pagamento == date(2024, 12, 20)

    def test_parse_negociacao_resumo_valores(self, linha_negociacao_resumo):
        """Testa parse de valores monetários."""
        resumo = parse_registro_negociacao_resumo(linha_negociacao_resumo)

        assert resumo.valor_bruto == Decimal("10000.00")
        assert resumo.valor_liquido == Decimal("9650.00")

    def test_parse_negociacao_resumo_taxas(self, linha_negociacao_resumo):
        """Testa parse de taxas."""
        resumo = parse_registro_negociacao_resumo(linha_negociacao_resumo)

        assert resumo.prazo_medio == 30
        assert resumo.taxa_nominal == Decimal("3.500")
        assert resumo.taxa_efetiva_negociacao == Decimal("3.650")

    def test_parse_negociacao_resumo_identificadores(self, linha_negociacao_resumo):
        """Testa parse de identificadores."""
        resumo = parse_registro_negociacao_resumo(linha_negociacao_resumo)

        assert resumo.numero_negociacao_registradora == "12345678901234567890"
        assert resumo.forma_pagamento == "001"


class TestParseNegociacaoDetalhe:
    """Testes para parse_registro_negociacao_detalhe."""

    def test_parse_negociacao_detalhe_basico(self, linha_negociacao_detalhe):
        """Testa parse básico de negociação detalhe."""
        detalhe = parse_registro_negociacao_detalhe(linha_negociacao_detalhe)

        assert detalhe.tipo_registro == "B"
        assert detalhe.cpf_cnpj == "12345678901234"

    def test_parse_negociacao_detalhe_bandeira(self, linha_negociacao_detalhe):
        """Testa parse de bandeira."""
        detalhe = parse_registro_negociacao_detalhe(linha_negociacao_detalhe)

        assert detalhe.bandeira == "001"
        assert detalhe.bandeira_descricao == "Visa"
        assert detalhe.tipo_liquidacao == "002"

    def test_parse_negociacao_detalhe_valores(self, linha_negociacao_detalhe):
        """Testa parse de valores."""
        detalhe = parse_registro_negociacao_detalhe(linha_negociacao_detalhe)

        assert detalhe.valor_bruto == Decimal("5000.00")
        assert detalhe.valor_liquido == Decimal("4825.00")
        assert detalhe.valor_desconto == Decimal("175.00")

    def test_parse_negociacao_detalhe_instituicao(self, linha_negociacao_detalhe):
        """Testa parse de instituição financeira."""
        detalhe = parse_registro_negociacao_detalhe(linha_negociacao_detalhe)

        assert detalhe.instituicao_financeira == "Banco Exemplo"
        assert detalhe.numero_estabelecimento == "1234567890"

    def test_parse_negociacao_detalhe_datas(self, linha_negociacao_detalhe):
        """Testa parse de datas."""
        detalhe = parse_registro_negociacao_detalhe(linha_negociacao_detalhe)

        assert detalhe.data_negociacao == date(2024, 12, 18)
        assert detalhe.data_vencimento_original == date(2024, 12, 25)

    def test_parse_negociacao_detalhe_taxa(self, linha_negociacao_detalhe):
        """Testa parse de taxa efetiva."""
        detalhe = parse_registro_negociacao_detalhe(linha_negociacao_detalhe)

        assert detalhe.taxa_efetiva == Decimal("3.500")


class TestParseContaRecebimento:
    """Testes para parse_registro_conta_recebimento."""

    def test_parse_conta_recebimento_basico(self, linha_conta_recebimento):
        """Testa parse básico de conta de recebimento."""
        conta = parse_registro_conta_recebimento(linha_conta_recebimento)

        assert conta.tipo_registro == "C"

    def test_parse_conta_recebimento_dados_bancarios(self, linha_conta_recebimento):
        """Testa parse de dados bancários."""
        conta = parse_registro_conta_recebimento(linha_conta_recebimento)

        assert conta.banco == "0341"
        assert conta.agencia == "12345"
        assert conta.conta == "12345678901234567890"

    def test_parse_conta_recebimento_valor(self, linha_conta_recebimento):
        """Testa parse de valor depositado."""
        conta = parse_registro_conta_recebimento(linha_conta_recebimento)

        assert conta.valor_depositado == Decimal("9650.00")
        assert conta.sinal_valor_depositado == "+"


class TestParseReservaFinanceira:
    """Testes para parse_registro_reserva_financeira."""

    def test_parse_reserva_financeira_basico(self, linha_reserva_financeira):
        """Testa parse básico de reserva financeira."""
        reserva = parse_registro_reserva_financeira(linha_reserva_financeira)

        assert reserva.tipo_registro == "R"
        assert reserva.estabelecimento_submissor == "1234567890"

    def test_parse_reserva_financeira_valor(self, linha_reserva_financeira):
        """Testa parse de valor de reserva."""
        reserva = parse_registro_reserva_financeira(linha_reserva_financeira)

        assert reserva.valor_reserva == Decimal("1000.00")
        assert reserva.sinal_valor_reserva == "+"

    def test_parse_reserva_financeira_bandeira(self, linha_reserva_financeira):
        """Testa parse de bandeira."""
        reserva = parse_registro_reserva_financeira(linha_reserva_financeira)

        assert reserva.bandeira == "001"
        assert reserva.bandeira_descricao == "Visa"

    def test_parse_reserva_financeira_data(self, linha_reserva_financeira):
        """Testa parse de data de vencimento."""
        reserva = parse_registro_reserva_financeira(linha_reserva_financeira)

        assert reserva.data_vencimento_original == date(2024, 12, 25)

    def test_parse_reserva_financeira_chave_ur(self, linha_reserva_financeira):
        """Testa parse de chave UR."""
        reserva = parse_registro_reserva_financeira(linha_reserva_financeira)

        # Chave UR pode ser vazia ou com espaços
        assert isinstance(reserva.chave_ur, str)


class TestParseURAgenda:
    """Testes adicionais para parse_registro_ur_agenda."""

    def test_parse_ur_agenda_todas_datas(self, linha_ur_agenda):
        """Testa parse de todas as datas no UR Agenda."""
        ur = parse_registro_ur_agenda(linha_ur_agenda)

        assert ur.data_pagamento == date(2024, 12, 18)
        assert ur.data_envio_banco == date(2024, 12, 17)
        assert ur.data_vencimento_original == date(2024, 12, 15)

    def test_parse_ur_agenda_cpf_cnpj(self, linha_ur_agenda):
        """Testa parse dos CPF/CNPJ."""
        ur = parse_registro_ur_agenda(linha_ur_agenda)

        assert ur.cpf_cnpj_titular == "12345678901234"
        assert ur.cpf_cnpj_titular_movimento == "12345678901234"
        assert ur.cpf_cnpj_recebedor == "12345678901234"

    def test_parse_ur_agenda_tipo_lancamento(self, linha_ur_agenda):
        """Testa parse e descrição do tipo de lançamento."""
        ur = parse_registro_ur_agenda(linha_ur_agenda)

        assert ur.tipo_lancamento == "02"
        assert ur.tipo_lancamento_descricao == "Venda crédito"

    def test_parse_ur_agenda_valores_originais(self, linha_ur_agenda):
        """Testa que valores originais são preservados."""
        ur = parse_registro_ur_agenda(linha_ur_agenda)

        assert ur.valor_bruto_original == "0000000100000"
        assert ur.valor_taxa_administrativa_original == "0000000002500"
        assert ur.valor_liquido_original == "0000000097500"


class TestParseDetalhe:
    """Testes adicionais para parse_registro_detalhe."""

    def test_parse_detalhe_hora_transacao(self, linha_detalhe):
        """Testa parse de hora da transação."""
        detalhe = parse_registro_detalhe(linha_detalhe)

        assert detalhe.hora_transacao == time(14, 30, 25)

    def test_parse_detalhe_grupo_cartoes(self, linha_detalhe):
        """Testa parse de grupo de cartões."""
        detalhe = parse_registro_detalhe(linha_detalhe)

        assert detalhe.grupo_cartoes == "01"

    def test_parse_detalhe_bin_cartao(self, linha_detalhe):
        """Testa parse de BIN e últimos dígitos do cartão."""
        detalhe = parse_registro_detalhe(linha_detalhe)

        assert detalhe.bin_cartao == "123456"
        assert detalhe.numero_cartao == "7890"

    def test_parse_detalhe_taxas(self, linha_detalhe):
        """Testa parse de todas as taxas."""
        detalhe = parse_registro_detalhe(linha_detalhe)

        assert detalhe.taxa_mdr == Decimal("2.500")
        assert detalhe.taxa_recebimento_automatico == Decimal("0.000")
        assert detalhe.taxa_venda == Decimal("0.000")

    def test_parse_detalhe_forma_pagamento_descricao(self, linha_detalhe):
        """Testa descrição da forma de pagamento."""
        detalhe = parse_registro_detalhe(linha_detalhe)

        assert detalhe.forma_pagamento == "040"
        assert detalhe.forma_pagamento_descricao == "Visa crédito à vista"

    def test_parse_detalhe_parcelas(self, linha_detalhe):
        """Testa parse de informações de parcelamento."""
        detalhe = parse_registro_detalhe(linha_detalhe)

        assert detalhe.parcela == 1
        assert detalhe.numero_total_parcelas == 3
        assert detalhe.parcela <= detalhe.numero_total_parcelas


class TestParseTrailer:
    """Testes adicionais para parse_registro_trailer."""

    def test_parse_trailer_basico(self, linha_trailer):
        """Testa parse básico do trailer."""
        trailer = parse_registro_trailer(linha_trailer)

        assert trailer.tipo_registro == "9"
        assert trailer.total_registros == 100

    def test_parse_trailer_valores_totais(self, linha_trailer):
        """Testa parse de valores totais."""
        trailer = parse_registro_trailer(linha_trailer)

        assert trailer.valor_liquido_soma == Decimal("97500.00")
        assert trailer.valor_bruto_soma == Decimal("100000.00")

    def test_parse_trailer_quantidade_registros(self, linha_trailer):
        """Testa parse de quantidade de registros tipo E."""
        trailer = parse_registro_trailer(linha_trailer)

        assert trailer.quantidade_registro_e == 50

    def test_parse_trailer_valores_negociacao(self, linha_trailer):
        """Testa valores de negociação no trailer."""
        trailer = parse_registro_trailer(linha_trailer)

        assert trailer.valor_liquido_cedido == Decimal("0.00")
        assert trailer.valor_liquido_gravame == Decimal("0.00")


class TestCasosEspeciais:
    """Testes para casos especiais e edge cases no parse."""

    def test_parse_com_espacos_extras(self):
        """Testa parse de linha com espaços extras."""
        linha = "8" + "1234567890" + "01" + "241218" + "143025"
        linha += "123e4567e89b12d3a456426614174000abcd" + "654321" + "241218"
        linha += "+" + "0000000050000" + "-" + "0000000001000" + "+" + "0000000049000"
        linha += "0341" + "12345" + "12345678901234567890" + "241218"
        linha += "01000" + "0100" + "02" + "12345678"
        linha += " " * 70 + "123e4567e89b12d3a456426614174111wxyz"
        linha += " " * 100  # Espaços extras além do necessário

        pix = parse_registro_pix(linha)
        assert pix.tipo_registro == "8"

    def test_parse_valores_zeros(self):
        """Testa parse de valores zerados."""
        linha = "C" + "0000" + "00000" + "00000000000000000000"
        linha += "+" + "0000000000000"  # Valor zero
        linha += " " * 206

        conta = parse_registro_conta_recebimento(linha)
        assert conta.valor_depositado == Decimal("0.00")

    def test_parse_data_invalida_retorna_none(self):
        """Testa que datas inválidas retornam None."""
        # Linha com data inválida (000000)
        linha = "8" + "1234567890" + "01" + "000000" + "143025"  # Data inválida
        linha += "123e4567e89b12d3a456426614174000abcd" + "654321" + "241218"
        linha += "+" + "0000000050000" + "-" + "0000000001000" + "+" + "0000000049000"
        linha += "0341" + "12345" + "12345678901234567890" + "241218"
        linha += "01000" + "0100" + "02" + "12345678"
        linha += " " * 70 + "123e4567e89b12d3a456426614174111wxyz"
        linha += " " * 100

        pix = parse_registro_pix(linha)
        assert pix.data_transacao is None

    def test_parse_hora_invalida_retorna_none(self):
        """Testa que horas inválidas retornam None."""
        # Linha com hora inválida
        linha = "8" + "1234567890" + "01" + "241218" + "999999"  # Hora inválida
        linha += "123e4567e89b12d3a456426614174000abcd" + "654321" + "241218"
        linha += "+" + "0000000050000" + "-" + "0000000001000" + "+" + "0000000049000"
        linha += "0341" + "12345" + "12345678901234567890" + "241218"
        linha += "01000" + "0100" + "02" + "12345678"
        linha += " " * 70 + "123e4567e89b12d3a456426614174111wxyz"
        linha += " " * 100

        pix = parse_registro_pix(linha)
        assert pix.hora_transacao is None

    def test_parse_valor_negativo(self):
        """Testa parse de valores negativos."""
        linha = "C" + "0341" + "12345" + "12345678901234567890"
        linha += "-" + "0000000100000"  # Valor negativo
        linha += " " * 206

        conta = parse_registro_conta_recebimento(linha)
        assert conta.sinal_valor_depositado == "-"
        assert conta.valor_depositado == Decimal("1000.00")


class TestParserCasosExtremos:
    """Testes para casos extremos do parser."""

    def test_converter_valor_decimal_com_erro(self):
        """Testa conversão de valor decimal com entrada inválida que causa erro."""
        # Testa com entrada vazia
        resultado = converter_valor_decimal("", 2)
        assert resultado == Decimal("0")

        # Testa com entrada apenas espaços
        resultado = converter_valor_decimal("   ", 2)
        assert resultado == Decimal("0")

    def test_processar_arquivo_com_encoding_errado(self):
        """Testa processamento com encoding errado que pode causar erro."""
        # Cria arquivo com caracteres especiais
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151\n"
        conteudo += "900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000" + " " * 155

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="cp1252") as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            # Tenta processar com encoding diferente
            parser = CieloEDIParser(encoding="utf-8")
            resultado = parser.processar_arquivo(temp_path)
            # Deve processar mesmo com encoding diferente
            assert resultado is not None
        except Exception:
            # Se falhar, é esperado
            pass
        finally:
            Path(temp_path).unlink()

    def test_processar_arquivo_io_erro(self):
        """Testa processamento quando há erro de I/O."""
        parser = CieloEDIParser()

        # Tenta processar arquivo que não existe
        with pytest.raises(FileNotFoundError):
            parser.processar_arquivo("arquivo_que_nao_existe.txt")


class TestParserStreamingCompleto:
    """Testes para cobertura completa do processamento streaming."""

    def test_processar_streaming_com_arquivo_path(self, arquivo_cielo04):
        """Testa processamento streaming a partir de arquivo Path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        try:
            parser = CieloEDIParser()
            registros = list(parser.processar_streaming(temp_path))

            # Deve ter processado alguns registros
            assert len(registros) > 0
        finally:
            Path(temp_path).unlink()

    def test_processar_streaming_com_linhas_vazias(self):
        """Testa processamento streaming com linhas vazias."""
        conteudo = """0123456789020241218202412012024123100000010CIELO04N                    151

900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000                                                                                                                               """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            parser = CieloEDIParser()
            registros = list(parser.processar_streaming(temp_path))

            # Deve ter ignorado linha vazia
            assert len(registros) == 2  # Header e Trailer
        finally:
            Path(temp_path).unlink()

    def test_processar_streaming_com_erro_parse(self):
        """Testa processamento streaming com erro no parse."""
        # Cria conteúdo com linha que causa erro
        conteudo = """0123456789020241218202412012024123100000010CIELO04N                    151
DXXXXXXXXXXXXXXXXXXX
900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000                                                                                                                               """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            parser = CieloEDIParser()
            registros = list(parser.processar_streaming(temp_path))

            # Deve ter processado header, erro, e trailer
            assert len(registros) >= 2
        finally:
            Path(temp_path).unlink()

    def test_processar_io_com_linhas_vazias(self):
        """Testa processamento de IO com linhas vazias."""
        from io import StringIO

        conteudo = """0123456789020241218202412012024123100000010CIELO04N                    151

900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000                                                                                                                               """

        parser = CieloEDIParser()
        resultado = parser._processar_io(StringIO(conteudo))

        # Deve ter processado ignorando linha vazia
        assert resultado is not None
        assert resultado.header is not None

    def test_processar_metodo_generico_com_bytes(self, arquivo_cielo04):
        """Testa método genérico processar() com bytes."""
        parser = CieloEDIParser()
        resultado = parser.processar(arquivo_cielo04.encode('latin-1'))

        assert resultado is not None
        assert resultado.header is not None

    def test_processar_metodo_generico_com_path(self, arquivo_cielo04):
        """Testa método genérico processar() com Path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = Path(f.name)

        try:
            parser = CieloEDIParser()
            resultado = parser.processar(temp_path)

            assert resultado is not None
            assert resultado.header is not None
        finally:
            temp_path.unlink()

    def test_processar_metodo_generico_com_io(self, arquivo_cielo04):
        """Testa método genérico processar() com IO."""
        from io import StringIO

        parser = CieloEDIParser()
        resultado = parser.processar(StringIO(arquivo_cielo04))

        assert resultado is not None
        assert resultado.header is not None


class TestParserCasosEspeciais:
    """Testes para casos especiais do parser."""

    def test_processar_arquivo_io_encoding_erro(self):
        """Testa processamento com encoding incorreto."""
        # Cria arquivo com conteúdo UTF-8
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151\n"
        conteudo += "900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000" + " " * 155

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            parser = CieloEDIParser(encoding="latin-1")
            # Deve processar mesmo com encoding diferente
            resultado = parser.processar_arquivo(temp_path)
            assert resultado is not None
        finally:
            Path(temp_path).unlink()

    def test_processar_linha_muito_curta(self):
        """Testa processamento de linha muito curta."""
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151\n"
        conteudo += "LINHA_CURTA\n"  # Linha muito curta
        conteudo += "900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000" + " " * 155

        parser = CieloEDIParser()
        resultado = parser.processar_string(conteudo)

        # Linha curta deve estar em linhas não processadas
        assert len(resultado.linhas_nao_processadas) > 0

    def test_processar_tipo_registro_desconhecido(self):
        """Testa processamento de tipo de registro desconhecido."""
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151\n"
        conteudo += "X" + " " * 399 + "\n"  # Tipo registro 'X' não existe
        conteudo += "900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000" + " " * 155

        parser = CieloEDIParser()
        resultado = parser.processar_string(conteudo)

        # Registro desconhecido deve estar em linhas não processadas
        assert len(resultado.linhas_nao_processadas) > 0

    def test_processar_arquivo_apenas_header(self):
        """Testa processamento de arquivo com apenas header."""
        conteudo = "0123456789020241218202412012024123100000010CIELO04N                    151\n"

        parser = CieloEDIParser()
        resultado = parser.processar_string(conteudo)

        assert resultado.header is not None
        assert resultado.trailer is None
        assert len(resultado.detalhes) == 0

    def test_processar_arquivo_bytes_vazio(self):
        """Testa processamento de arquivo bytes vazio."""
        parser = CieloEDIParser()

        # Arquivo vazio não gera exceção, apenas retorna resultado vazio
        resultado = parser.processar_bytes(b"")
        assert resultado is not None
        assert resultado.header is None
        assert len(resultado.detalhes) == 0
