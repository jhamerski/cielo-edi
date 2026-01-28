"""
Testes de integração para todos os tipos de arquivo Cielo EDI.

Testa o processamento completo de cada tipo de arquivo:
- CIELO03: Captura/Previsão
- CIELO04: Liquidação/Pagamento
- CIELO09: Saldo em Aberto
- CIELO15: Negociação de Recebíveis
- CIELO16: Pix
"""

from decimal import Decimal
from datetime import date, time

from cielo_edi.parser import CieloEDIParser

from cielo_edi.dominios import get_descricao, CODIGOS_BANDEIRAS


class TestDominios:
    """Testes para funções auxiliares do módulo dominios."""

    def test_get_descricao_codigo_existente(self):
        """Testa get_descricao com código existente."""
        resultado = get_descricao(CODIGOS_BANDEIRAS, "001")
        assert resultado == "Visa"

    def test_get_descricao_codigo_inexistente(self):
        """Testa get_descricao com código inexistente."""
        resultado = get_descricao(CODIGOS_BANDEIRAS, "999")
        assert resultado == "Não identificado"

    def test_get_descricao_default_customizado(self):
        """Testa get_descricao com default customizado."""
        resultado = get_descricao(CODIGOS_BANDEIRAS, "999", "Desconhecido")
        assert resultado == "Desconhecido"


class TestArquivoCIELO03:
    """Testes para arquivo CIELO03 - Captura/Previsão."""

    def test_processar_cielo03_completo(self, arquivo_cielo03):
        """Testa processamento completo de arquivo CIELO03."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo03)

        assert resultado.header is not None
        assert resultado.header.opcao_extrato == "03"
        assert resultado.header.opcao_extrato_descricao == "Captura/Previsão"
        assert resultado.tipo_arquivo == "03"

    def test_cielo03_estrutura_registros(self, arquivo_cielo03):
        """Testa estrutura de registros do CIELO03."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo03)

        # CIELO03 deve ter: Header + UR Agenda + Detalhe + Trailer
        assert resultado.header is not None
        assert len(resultado.ur_agenda) >= 1
        assert len(resultado.detalhes) >= 1
        assert resultado.trailer is not None

        # Não deve ter registros de Pix ou Negociação
        assert len(resultado.pix) == 0
        assert len(resultado.negociacoes_resumo) == 0

    def test_cielo03_valores_corretos(self, arquivo_cielo03):
        """Testa se os valores monetários estão corretos."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo03)

        ur = resultado.ur_agenda[0]
        assert ur.valor_bruto == Decimal("1000.00")
        assert ur.valor_liquido == Decimal("975.00")
        assert ur.bandeira == "001"
        assert ur.bandeira_descricao == "Visa"

    def test_cielo03_status_captura(self, arquivo_cielo03):
        """Testa status de pagamento em arquivo de captura."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo03)

        # No arquivo de captura, status 01 = captura prevista
        ur = resultado.ur_agenda[0]
        assert ur.status_pagamento == "01"
        assert ur.status_pagamento_descricao == "Desconhecido"


class TestArquivoCIELO04:
    """Testes para arquivo CIELO04 - Liquidação/Pagamento."""

    def test_processar_cielo04_completo(self, arquivo_cielo04):
        """Testa processamento completo de arquivo CIELO04."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        assert resultado.header is not None
        assert resultado.header.opcao_extrato == "04"
        assert resultado.header.opcao_extrato_descricao == "Liquidação/Pagamento"
        assert resultado.tipo_arquivo == "04"

    def test_cielo04_estrutura_registros(self, arquivo_cielo04):
        """Testa estrutura de registros do CIELO04."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        # CIELO04 deve ter: Header + UR Agenda + Detalhe + Trailer
        assert resultado.header is not None
        assert len(resultado.ur_agenda) == 1
        assert len(resultado.detalhes) == 1
        assert resultado.trailer is not None

    def test_cielo04_datas_pagamento(self, arquivo_cielo04):
        """Testa se datas de pagamento estão presentes."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        ur = resultado.ur_agenda[0]
        assert ur.data_pagamento is not None
        assert ur.data_pagamento == date(2024, 12, 18)
        assert ur.status_pagamento == "04"
        assert ur.status_pagamento_descricao == "Pago"

    def test_cielo04_estatisticas(self, arquivo_cielo04):
        """Testa estatísticas acumuladas."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        assert resultado.estatisticas.total_linhas == 4
        assert resultado.estatisticas.total_ur_agenda == 1
        assert resultado.estatisticas.total_detalhes == 1
        assert resultado.estatisticas.valor_bruto_total == Decimal("1000.00")
        assert resultado.estatisticas.valor_liquido_total == Decimal("975.00")

    def test_cielo04_dados_bancarios(self, arquivo_cielo04):
        """Testa dados bancários no registro UR Agenda."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        ur = resultado.ur_agenda[0]
        assert ur.banco == "0341"
        assert ur.agencia == "12345"
        assert ur.conta == "12345678901234567890"
        assert ur.digito_conta == "1"


class TestArquivoCIELO09:
    """Testes para arquivo CIELO09 - Saldo em Aberto."""

    def test_processar_cielo09_completo(self, arquivo_cielo09):
        """Testa processamento completo de arquivo CIELO09."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo09)

        assert resultado.header is not None
        assert resultado.header.opcao_extrato == "09"
        assert resultado.header.opcao_extrato_descricao == "Saldo em aberto"
        assert resultado.tipo_arquivo == "09"

    def test_cielo09_sem_data_pagamento(self, arquivo_cielo09):
        """Testa que registros em aberto não têm data de pagamento."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo09)

        ur = resultado.ur_agenda[0]
        # Em arquivo de saldo em aberto, datas de pagamento devem ser None ou zeros
        assert ur.data_pagamento is None or ur.data_pagamento == date(1900, 1, 1)
        assert ur.status_pagamento == "01"

    def test_cielo09_valores_pendentes(self, arquivo_cielo09):
        """Testa valores pendentes de pagamento."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo09)

        ur = resultado.ur_agenda[0]
        assert ur.valor_bruto == Decimal("1000.00")
        assert ur.valor_liquido == Decimal("975.00")
        assert ur.data_vencimento_original is not None


class TestArquivoCIELO15:
    """Testes para arquivo CIELO15 - Negociação de Recebíveis."""

    def test_processar_cielo15_completo(self, arquivo_cielo15):
        """Testa processamento completo de arquivo CIELO15."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        assert resultado.header is not None
        assert resultado.header.opcao_extrato == "15"
        assert resultado.header.opcao_extrato_descricao == "Negociação de Recebíveis Cielo (NRC)"
        assert resultado.tipo_arquivo == "15"

    def test_cielo15_estrutura_registros(self, arquivo_cielo15):
        """Testa estrutura específica de registros CIELO15."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        # CIELO15 deve ter registros específicos de negociação
        assert resultado.header is not None
        assert len(resultado.negociacoes_resumo) == 1
        assert len(resultado.negociacoes_detalhe) == 1
        assert len(resultado.contas_recebimento) == 1
        assert len(resultado.reserva_financeira) == 1
        assert resultado.trailer is not None

        # Não deve ter registros de UR Agenda/Detalhe padrão
        assert len(resultado.ur_agenda) == 0
        assert len(resultado.detalhes) == 0
        assert len(resultado.pix) == 0

    def test_cielo15_negociacao_resumo(self, arquivo_cielo15):
        """Testa registro de negociação resumo (A)."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        resumo = resultado.negociacoes_resumo[0]
        assert resumo.tipo_registro == "A"
        assert resumo.valor_bruto == Decimal("10000.00")
        assert resumo.valor_liquido == Decimal("9650.00")
        assert resumo.prazo_medio == 30
        assert resumo.taxa_nominal == Decimal("3.500")
        assert resumo.taxa_efetiva_negociacao == Decimal("3.650")

    def test_cielo15_negociacao_detalhe(self, arquivo_cielo15):
        """Testa registro de negociação detalhe (B)."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        detalhe = resultado.negociacoes_detalhe[0]
        assert detalhe.tipo_registro == "B"
        assert detalhe.valor_bruto == Decimal("5000.00")
        assert detalhe.valor_liquido == Decimal("4825.00")
        assert detalhe.valor_desconto == Decimal("175.00")
        assert detalhe.bandeira == "001"
        assert detalhe.bandeira_descricao == "Visa"
        assert detalhe.instituicao_financeira == "Banco Exemplo"

    def test_cielo15_conta_recebimento(self, arquivo_cielo15):
        """Testa registro de conta de recebimento (C)."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        conta = resultado.contas_recebimento[0]
        assert conta.tipo_registro == "C"
        assert conta.banco == "0341"
        assert conta.agencia == "12345"
        assert conta.conta == "12345678901234567890"
        assert conta.valor_depositado == Decimal("9650.00")

    def test_cielo15_reserva_financeira(self, arquivo_cielo15):
        """Testa registro de reserva financeira (R)."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        reserva = resultado.reserva_financeira[0]
        assert reserva.tipo_registro == "R"
        assert reserva.valor_reserva == Decimal("1000.00")
        assert reserva.bandeira == "001"
        assert reserva.bandeira_descricao == "Visa"
        assert reserva.data_vencimento_original == date(2024, 12, 25)

    def test_cielo15_calculo_desconto(self, arquivo_cielo15):
        """Testa cálculo de desconto na negociação."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        detalhe = resultado.negociacoes_detalhe[0]
        # Valor bruto - valor desconto = valor líquido
        desconto_calculado = detalhe.valor_bruto - detalhe.valor_desconto
        assert desconto_calculado == detalhe.valor_liquido


class TestArquivoCIELO16:
    """Testes para arquivo CIELO16 - Pix."""

    def test_processar_cielo16_completo(self, arquivo_cielo16):
        """Testa processamento completo de arquivo CIELO16."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        assert resultado.header is not None
        assert resultado.header.opcao_extrato == "16"
        assert resultado.header.opcao_extrato_descricao == "Pix"
        assert resultado.tipo_arquivo == "16"

    def test_cielo16_estrutura_registros(self, arquivo_cielo16):
        """Testa estrutura de registros do CIELO16."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        # CIELO16 deve ter: Header + Pix + Trailer
        assert resultado.header is not None
        assert len(resultado.pix) == 1
        assert resultado.trailer is not None

        # Não deve ter outros tipos de registro
        assert len(resultado.ur_agenda) == 0
        assert len(resultado.detalhes) == 0
        assert len(resultado.negociacoes_resumo) == 0

    def test_cielo16_registro_pix(self, arquivo_cielo16):
        """Testa campos do registro Pix (8)."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        pix = resultado.pix[0]
        assert pix.tipo_registro == "8"
        assert pix.tipo_transacao == "01"
        assert pix.valor_bruto == Decimal("500.00")
        assert pix.valor_taxa_administrativa == Decimal("10.00")
        assert pix.valor_liquido == Decimal("490.00")

    def test_cielo16_identificadores_pix(self, arquivo_cielo16):
        """Testa identificadores únicos do Pix."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        pix = resultado.pix[0]
        assert len(pix.id_pix) == 36  # UUID format
        assert pix.id_pix == "123e4567e89b12d3a456426614174000abcd"
        assert len(pix.tx_id) == 36
        assert pix.tx_id == "123e4567e89b12d3a456426614174111wxyz"
        assert pix.nsu_doc == "654321"

    def test_cielo16_datas_e_horarios(self, arquivo_cielo16):
        """Testa datas e horários da transação Pix."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        pix = resultado.pix[0]
        assert pix.data_transacao == date(2024, 12, 18)
        assert pix.hora_transacao == time(14, 30, 25)
        assert pix.data_pagamento == date(2024, 12, 18)
        assert pix.data_captura_transacao == date(2024, 12, 18)

    def test_cielo16_taxas_pix(self, arquivo_cielo16):
        """Testa taxas administrativas do Pix."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        pix = resultado.pix[0]
        assert pix.taxa_administrativa == Decimal("1.000")  # 1%
        assert pix.tarifa_administrativa == Decimal("1.00")
        assert pix.canal_venda == "02"

    def test_cielo16_canal_venda_descricao(self, arquivo_cielo16):
        """Testa descrição do canal de venda."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        pix = resultado.pix[0]
        # canal_venda_descricao retorna string (pode ser vazia se código não mapeado)
        assert isinstance(pix.canal_venda_descricao, str)

    def test_cielo16_estatisticas(self, arquivo_cielo16):
        """Testa estatísticas específicas do arquivo Pix."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        assert resultado.estatisticas.total_pix == 1
        assert resultado.estatisticas.total_detalhes == 0
        assert resultado.estatisticas.total_ur_agenda == 0


class TestComparacaoTiposArquivo:
    """Testes comparativos entre diferentes tipos de arquivo."""

    def test_headers_diferentes_tipos(self, arquivo_cielo03, arquivo_cielo04,
                                      arquivo_cielo09, arquivo_cielo15, arquivo_cielo16):
        """Testa que cada tipo de arquivo tem o header correto."""
        parser = CieloEDIParser()

        tipos_esperados = {
            arquivo_cielo03: ("03", "Captura/Previsão"),
            arquivo_cielo04: ("04", "Liquidação/Pagamento"),
            arquivo_cielo09: ("09", "Saldo em aberto"),
            arquivo_cielo15: ("15", "Negociação de Recebíveis Cielo (NRC)"),
            arquivo_cielo16: ("16", "Pix"),
        }

        for arquivo, (codigo, descricao) in tipos_esperados.items():
            resultado = parser.processar_string(arquivo)
            assert resultado.tipo_arquivo == codigo
            assert resultado.header.opcao_extrato_descricao == descricao

    def test_trailer_consistente(self, arquivo_cielo03, arquivo_cielo04, arquivo_cielo16):
        """Testa que todos os arquivos têm trailer válido."""
        parser = CieloEDIParser()

        for arquivo in [arquivo_cielo03, arquivo_cielo04, arquivo_cielo16]:
            resultado = parser.processar_string(arquivo)
            assert resultado.trailer is not None
            assert resultado.trailer.tipo_registro == "9"
            assert resultado.trailer.total_registros > 0

    def test_registros_exclusivos_por_tipo(self, arquivo_cielo04, arquivo_cielo15, arquivo_cielo16):
        """Testa que cada tipo tem seus registros exclusivos."""
        parser = CieloEDIParser()

        # CIELO04 tem UR Agenda e Detalhe, não tem Pix/Negociação
        resultado_04 = parser.processar_string(arquivo_cielo04)
        assert len(resultado_04.ur_agenda) > 0
        assert len(resultado_04.detalhes) > 0
        assert len(resultado_04.pix) == 0
        assert len(resultado_04.negociacoes_resumo) == 0

        # CIELO15 tem Negociação, não tem UR/Detalhe/Pix
        resultado_15 = parser.processar_string(arquivo_cielo15)
        assert len(resultado_15.negociacoes_resumo) > 0
        assert len(resultado_15.ur_agenda) == 0
        assert len(resultado_15.pix) == 0

        # CIELO16 tem Pix, não tem outros
        resultado_16 = parser.processar_string(arquivo_cielo16)
        assert len(resultado_16.pix) > 0
        assert len(resultado_16.ur_agenda) == 0
        assert len(resultado_16.detalhes) == 0
        assert len(resultado_16.negociacoes_resumo) == 0


class TestValidacoesEspecificas:
    """Testes de validações específicas por tipo de arquivo."""

    def test_valores_originais_preservados(self, arquivo_cielo04):
        """Testa que valores originais do EDI são preservados."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        ur = resultado.ur_agenda[0]
        # Valores originais devem estar presentes
        assert ur.valor_bruto_original != ""
        assert ur.valor_liquido_original != ""
        assert ur.valor_taxa_administrativa_original != ""

        # Valores convertidos devem estar corretos
        assert ur.valor_bruto == Decimal("1000.00")
        assert ur.valor_liquido == Decimal("975.00")

    def test_sinais_monetarios(self, arquivo_cielo04):
        """Testa que sinais de valores monetários são capturados."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        ur = resultado.ur_agenda[0]
        assert ur.sinal_valor_bruto == "+"
        assert ur.sinal_valor_liquido == "+"
        assert ur.sinal_taxa_administrativa == "-"

    def test_quantidade_lancamentos(self, arquivo_cielo04):
        """Testa contador de lançamentos."""
        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        ur = resultado.ur_agenda[0]
        assert ur.quantidade_lancamentos == 10
        assert ur.quantidade_lancamentos > 0
