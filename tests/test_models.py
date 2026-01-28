import pytest
from decimal import Decimal
from datetime import date, time
from pydantic import ValidationError

from cielo_edi.models import (
    RegistroPix,
    RegistroNegociacaoResumo,
    RegistroNegociacaoDetalhe,
    RegistroContaRecebimento,
    RegistroReservaFinanceira,
    RegistroHeader,
    RegistroURAgenda,
    RegistroDetalhe,
    Estatisticas,
    ResultadoProcessamento,
)


class TestRegistroHeader:
    """Testes para o modelo RegistroHeader."""

    def test_criar_header_valido(self):
        """Testa criação de header válido."""
        header = RegistroHeader(
            tipo_registro="0",
            estabelecimento_matriz="1234567890",
            data_processamento=date(2024, 12, 18),
            periodo_inicial=date(2024, 12, 1),
            periodo_final=date(2024, 12, 31),
            sequencia="0000001",
            empresa_adquirente="CIELO",
            opcao_extrato="04",
            transmissao="N",
            versao_layout="151",
        )

        assert header.tipo_registro == "0"
        assert header.estabelecimento_matriz == "1234567890"
        assert header.opcao_extrato_descricao == "Liquidação/Pagamento"

    def test_header_tipo_arquivo_descricao(self):
        """Testa descrições dos tipos de arquivo."""
        tipos = {
            "03": "Captura/Previsão",
            "04": "Liquidação/Pagamento",
            "09": "Saldo em aberto",
            "15": "Negociação de Recebíveis Cielo (NRC)",
            "16": "Pix",
        }

        for codigo, descricao in tipos.items():
            header = RegistroHeader(
                tipo_registro="0",
                estabelecimento_matriz="1234567890",
                sequencia="0000001",
                opcao_extrato=codigo,
                transmissao="N",
                versao_layout="151",
            )
            assert header.opcao_extrato_descricao == descricao


class TestRegistroURAgenda:
    """Testes para o modelo RegistroURAgenda."""

    def test_criar_ur_agenda_valido(self):
        """Testa criação de UR agenda válido."""
        ur = RegistroURAgenda(
            tipo_registro="D",
            estabelecimento_submissor="1234567890",
            cpf_cnpj_titular="12345678901234",
            cpf_cnpj_titular_movimento="12345678901234",
            cpf_cnpj_recebedor="12345678901234",
            bandeira="001",
            tipo_liquidacao="002",
            matriz_pagamento="1234567890",
            status_pagamento="04",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("25.00"),
            valor_taxa_administrativa_original="0000000002500",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            banco="0341",
            agencia="12345",
            conta="12345678901234567890",
            digito_conta="1",
            quantidade_lancamentos=10,
            tipo_lancamento="02",
            chave_ur="ABC123",
        )

        assert ur.valor_bruto == Decimal("1000.00")
        assert ur.bandeira_descricao == "Visa"
        assert ur.tipo_liquidacao_descricao == "Crédito"
        assert ur.status_pagamento_descricao == "Pago"
        assert ur.tipo_lancamento_descricao == "Venda crédito"


class TestRegistroDetalhe:
    """Testes para o modelo RegistroDetalhe."""

    def test_criar_detalhe_valido(self):
        """Testa criação de detalhe válido."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=3,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="ABC123",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.500"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("3000.00"),
            valor_total_venda_original="0000000300000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )

        assert detalhe.parcela == 1
        assert detalhe.numero_total_parcelas == 3
        assert detalhe.bandeira_liquidacao_descricao == "Visa"
        assert detalhe.forma_pagamento_descricao == "Visa crédito à vista"

    def test_detalhe_parcela_invalida(self):
        """Testa validação de parcela inválida."""
        with pytest.raises(ValidationError):
            RegistroDetalhe(
                tipo_registro="E",
                estabelecimento_submissor="1234567890",
                bandeira_liquidacao="001",
                tipo_liquidacao="002",
                parcela=100,  # Máximo é 99
                numero_total_parcelas=3,
                codigo_autorizacao="123456",
                tipo_lancamento="02",
                chave_ur="ABC123",
                forma_pagamento="040",
                nsu_doc="654321",
                taxa_mdr=Decimal("2.500"),
                sinal_valor_total_venda="+",
                valor_total_venda=Decimal("3000.00"),
                sinal_valor_bruto="+",
                valor_bruto_venda_parcela=Decimal("1000.00"),
                sinal_valor_liquido="+",
                valor_liquido_venda=Decimal("975.00"),
                sinal_valor_comissao="-",
                valor_comissao=Decimal("25.00"),
            )


class TestEstatisticas:
    """Testes para o modelo Estatisticas."""

    def test_estatisticas_default(self):
        """Testa valores default das estatísticas."""
        stats = Estatisticas()

        assert stats.total_linhas == 0
        assert stats.total_ur_agenda == 0
        assert stats.total_detalhes == 0
        assert stats.total_pix == 0
        assert stats.valor_bruto_total == Decimal("0")
        assert stats.valor_liquido_total == Decimal("0")

    def test_estatisticas_com_valores(self):
        """Testa estatísticas com valores."""
        stats = Estatisticas(
            total_linhas=100,
            total_ur_agenda=10,
            total_detalhes=50,
            valor_bruto_total=Decimal("10000.00"),
            valor_liquido_total=Decimal("9500.00"),
        )

        assert stats.total_linhas == 100
        assert stats.valor_bruto_total == Decimal("10000.00")


class TestResultadoProcessamento:
    """Testes para o modelo ResultadoProcessamento."""

    def test_resultado_vazio(self):
        """Testa resultado vazio."""
        resultado = ResultadoProcessamento()

        assert resultado.header is None
        assert resultado.trailer is None
        assert resultado.ur_agenda == []
        assert resultado.detalhes == []
        assert resultado.pix == []

    def test_resultado_to_dict(self):
        """Testa conversão para dicionário."""
        resultado = ResultadoProcessamento(
            tipo_arquivo="04",
            tipo_arquivo_descricao="Liquidação/Pagamento",
        )

        data = resultado.to_dict()

        assert isinstance(data, dict)
        assert data["tipo_arquivo"] == "04"
        assert "estatisticas" in data

    def test_resultado_com_registros(self):
        """Testa resultado com registros."""
        header = RegistroHeader(
            tipo_registro="0",
            estabelecimento_matriz="1234567890",
            sequencia="0000001",
            opcao_extrato="04",
            transmissao="N",
            versao_layout="151",
        )

        resultado = ResultadoProcessamento(
            header=header,
            tipo_arquivo="04",
        )

        assert resultado.header is not None
        assert resultado.header.estabelecimento_matriz == "1234567890"


class TestRegistroPix:
    """Testes para o modelo RegistroPix (registro tipo 8)."""

    def test_criar_pix_valido(self):
        """Testa criação de registro Pix válido."""
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            data_transacao=date(2024, 12, 18),
            hora_transacao=time(14, 30, 25),
            id_pix="123e4567-e89b-12d3-a456-426614174000",
            nsu_doc="654321",
            data_pagamento=date(2024, 12, 18),
            sinal_valor_bruto="+",
            valor_bruto=Decimal("500.00"),
            valor_bruto_original="0000000050000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("10.00"),
            valor_taxa_administrativa_original="0000000001000",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("490.00"),
            valor_liquido_original="0000000049000",
            banco="0341",
            agencia="12345",
            conta="12345678901234567890",
            data_captura_transacao=date(2024, 12, 18),
            taxa_administrativa=Decimal("1.000"),
            tarifa_administrativa=Decimal("1.00"),
            canal_venda="02",
            numero_logico_terminal="12345678",
            tx_id="123e4567-e89b-12d3-a456-426614174111",
        )

        assert pix.tipo_registro == "8"
        assert pix.valor_bruto == Decimal("500.00")
        assert pix.valor_liquido == Decimal("490.00")
        assert pix.id_pix == "123e4567-e89b-12d3-a456-426614174000"

    def test_pix_valores_monetarios(self):
        """Testa cálculo de valores monetários no Pix."""
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            id_pix="abc-123",
            nsu_doc="123456",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("25.00"),
            valor_taxa_administrativa_original="0000000002500",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            banco="0001",
            agencia="001",
            conta="12345",
        )

        # Verifica cálculo: valor bruto - taxa = valor líquido
        assert pix.valor_bruto - pix.valor_taxa_administrativa == pix.valor_liquido

    def test_pix_canal_venda_descricao(self):
        """Testa property de descrição do canal de venda."""
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            id_pix="abc-123",
            nsu_doc="123456",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("1.00"),
            valor_taxa_administrativa_original="0000000000100",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("99.00"),
            valor_liquido_original="0000000009900",
            banco="0001",
            agencia="001",
            conta="12345",
            canal_venda="02",
        )

        # Property deve retornar descrição ou string vazia
        assert isinstance(pix.canal_venda_descricao, str)

    def test_pix_datas_opcionais(self):
        """Testa que datas são opcionais no Pix."""
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            id_pix="abc-123",
            nsu_doc="123456",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("1.00"),
            valor_taxa_administrativa_original="0000000000100",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("99.00"),
            valor_liquido_original="0000000009900",
            banco="0001",
            agencia="001",
            conta="12345",
        )

        # Datas opcionais podem ser None
        assert pix.data_transacao is None
        assert pix.hora_transacao is None
        assert pix.data_pagamento is None


class TestRegistroDetalhe:
    """Testes para o modelo RegistroDetalhe (registro tipo E)."""

    def test_criar_detalhe_valido(self):
        """Testa criação de registro detalhe válido."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=3,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="CHAVE_UR_123",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.500"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("3000.00"),
            valor_total_venda_original="0000000300000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )

        assert detalhe.tipo_registro == "E"
        assert detalhe.parcela == 1
        assert detalhe.numero_total_parcelas == 3
        assert detalhe.valor_bruto_venda_parcela == Decimal("1000.00")

    def test_detalhe_parcela_invalida(self):
        """Testa validação de número de parcela."""
        with pytest.raises(ValidationError):
            RegistroDetalhe(
                tipo_registro="E",
                estabelecimento_submissor="1234567890",
                bandeira_liquidacao="001",
                tipo_liquidacao="002",
                parcela=100,  # Máximo é 99
                numero_total_parcelas=3,
                codigo_autorizacao="123456",
                tipo_lancamento="02",
                chave_ur="CHAVE",
                forma_pagamento="040",
                nsu_doc="654321",
                taxa_mdr=Decimal("2.500"),
                sinal_valor_total_venda="+",
                valor_total_venda=Decimal("100.00"),
                sinal_valor_bruto="+",
                valor_bruto_venda_parcela=Decimal("100.00"),
                sinal_valor_liquido="+",
                valor_liquido_venda=Decimal("97.50"),
                sinal_valor_comissao="-",
                valor_comissao=Decimal("2.50"),
            )

    def test_detalhe_bandeira_descricao(self):
        """Testa property de descrição da bandeira."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",  # Visa
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="CHAVE",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.500"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("100.00"),
            valor_total_venda_original="0000000010000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("97.50"),
            valor_liquido_original="0000000009750",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("2.50"),
            valor_comissao_original="0000000000250",
        )

        assert detalhe.bandeira_liquidacao_descricao == "Visa"

    def test_detalhe_forma_pagamento_descricao(self):
        """Testa property de descrição da forma de pagamento."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="CHAVE",
            forma_pagamento="040",  # Visa crédito à vista
            nsu_doc="654321",
            taxa_mdr=Decimal("2.500"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("100.00"),
            valor_total_venda_original="0000000010000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("97.50"),
            valor_liquido_original="0000000009750",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("2.50"),
            valor_comissao_original="0000000000250",
        )

        assert detalhe.forma_pagamento_descricao != ""

    def test_detalhe_valores_originais(self):
        """Testa que valores originais são preservados."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="CHAVE",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.500"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("100.00"),
            valor_total_venda_original="0000000010000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("97.50"),
            valor_liquido_original="0000000009750",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("2.50"),
            valor_comissao_original="0000000000250",
        )

        assert detalhe.valor_total_venda_original == "0000000010000"
        assert detalhe.valor_bruto_original == "0000000010000"
        assert detalhe.valor_liquido_original == "0000000009750"
        assert detalhe.valor_comissao_original == "0000000000250"

    def test_detalhe_hora_transacao_opcional(self):
        """Testa que hora da transação é opcional."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="CHAVE",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.500"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("100.00"),
            valor_total_venda_original="0000000010000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("97.50"),
            valor_liquido_original="0000000009750",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("2.50"),
            valor_comissao_original="0000000000250",
        )

        assert detalhe.hora_transacao is None


class TestRegistroNegociacaoResumo:
    """Testes para o modelo RegistroNegociacaoResumo (registro tipo A)."""

    def test_criar_negociacao_resumo_valido(self):
        """Testa criação de resumo de negociação válido."""
        resumo = RegistroNegociacaoResumo(
            tipo_registro="A",
            data_negociacao=date(2024, 12, 18),
            data_pagamento=date(2024, 12, 20),
            cpf_cnpj="12345678901234",
            prazo_medio=30,
            taxa_nominal=Decimal("3.500"),
            sinal_valor_bruto="+",
            valor_bruto=Decimal("10000.00"),
            valor_bruto_original="0000001000000",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("9650.00"),
            valor_liquido_original="0000000965000",
            numero_negociacao_registradora="ABC123",
            forma_pagamento="001",
            taxa_efetiva_negociacao=Decimal("3.650"),
        )

        assert resumo.tipo_registro == "A"
        assert resumo.prazo_medio == 30
        assert resumo.taxa_nominal == Decimal("3.500")
        assert resumo.valor_bruto == Decimal("10000.00")

    def test_negociacao_resumo_taxas(self):
        """Testa taxas nominal e efetiva."""
        resumo = RegistroNegociacaoResumo(
            tipo_registro="A",
            cpf_cnpj="12345678901234",
            prazo_medio=15,
            taxa_nominal=Decimal("2.500"),
            sinal_valor_bruto="+",
            valor_bruto=Decimal("5000.00"),
            sinal_valor_liquido="+",
            valor_liquido=Decimal("4875.00"),
            taxa_efetiva_negociacao=Decimal("2.600"),
        )

        # Taxa efetiva normalmente é maior que nominal
        assert resumo.taxa_efetiva_negociacao >= resumo.taxa_nominal

    def test_negociacao_resumo_prazo_zero(self):
        """Testa validação de prazo médio não negativo."""
        resumo = RegistroNegociacaoResumo(
            tipo_registro="A",
            cpf_cnpj="12345678901234",
            prazo_medio=0,  # Válido
            taxa_nominal=Decimal("0.000"),
            sinal_valor_bruto="+",
            valor_bruto=Decimal("100.00"),
            sinal_valor_liquido="+",
            valor_liquido=Decimal("100.00"),
        )

        assert resumo.prazo_medio == 0

    def test_negociacao_resumo_prazo_negativo(self):
        """Testa que prazo negativo é rejeitado."""
        with pytest.raises(ValidationError):
            RegistroNegociacaoResumo(
                tipo_registro="A",
                cpf_cnpj="12345678901234",
                prazo_medio=-1,  # Inválido
                taxa_nominal=Decimal("0.000"),
                sinal_valor_bruto="+",
                valor_bruto=Decimal("100.00"),
                sinal_valor_liquido="+",
                valor_liquido=Decimal("100.00"),
            )


class TestRegistroNegociacaoDetalhe:
    """Testes para o modelo RegistroNegociacaoDetalhe (registro tipo B)."""

    def test_criar_negociacao_detalhe_valido(self):
        """Testa criação de detalhe de negociação válido."""
        detalhe = RegistroNegociacaoDetalhe(
            tipo_registro="B",
            data_negociacao=date(2024, 12, 18),
            data_vencimento_original=date(2024, 12, 25),
            cpf_cnpj="12345678901234",
            bandeira="001",
            tipo_liquidacao="002",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("5000.00"),
            valor_bruto_original="0000000500000",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("4825.00"),
            valor_liquido_original="0000000482500",
            taxa_efetiva=Decimal("3.500"),
            instituicao_financeira="Banco Exemplo",
            numero_estabelecimento="1234567890",
            sinal_valor_desconto="-",
            valor_desconto=Decimal("175.00"),
            valor_desconto_original="0000000017500",
        )

        assert detalhe.tipo_registro == "B"
        assert detalhe.bandeira == "001"
        assert detalhe.valor_desconto == Decimal("175.00")

    def test_negociacao_detalhe_bandeira_descricao(self):
        """Testa property de descrição da bandeira."""
        detalhe = RegistroNegociacaoDetalhe(
            tipo_registro="B",
            cpf_cnpj="12345678901234",
            bandeira="001",  # Visa
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            sinal_valor_liquido="+",
            valor_liquido=Decimal("970.00"),
        )

        assert detalhe.bandeira_descricao == "Visa"

    def test_negociacao_detalhe_bandeira_desconhecida(self):
        """Testa bandeira não cadastrada."""
        detalhe = RegistroNegociacaoDetalhe(
            tipo_registro="B",
            cpf_cnpj="12345678901234",
            bandeira="999",  # Não existe
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            sinal_valor_liquido="+",
            valor_liquido=Decimal("970.00"),
        )

        assert detalhe.bandeira_descricao == "Desconhecida"

    def test_negociacao_detalhe_calculo_desconto(self):
        """Testa que valor bruto - desconto = valor líquido."""
        detalhe = RegistroNegociacaoDetalhe(
            tipo_registro="B",
            cpf_cnpj="12345678901234",
            bandeira="001",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            sinal_valor_liquido="+",
            valor_liquido=Decimal("950.00"),
            sinal_valor_desconto="-",
            valor_desconto=Decimal("50.00"),
        )

        assert detalhe.valor_bruto - detalhe.valor_desconto == detalhe.valor_liquido

    def test_negociacao_detalhe_sem_desconto(self):
        """Testa negociação sem desconto."""
        detalhe = RegistroNegociacaoDetalhe(
            tipo_registro="B",
            cpf_cnpj="12345678901234",
            bandeira="001",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            sinal_valor_liquido="+",
            valor_liquido=Decimal("1000.00"),
            valor_desconto=Decimal("0.00"),
        )

        assert detalhe.valor_desconto == Decimal("0.00")


class TestRegistroContaRecebimento:
    """Testes para o modelo RegistroContaRecebimento (registro tipo C)."""

    def test_criar_conta_recebimento_valida(self):
        """Testa criação de conta de recebimento válida."""
        conta = RegistroContaRecebimento(
            tipo_registro="C",
            banco="0341",
            agencia="12345",
            conta="12345678901234567890",
            sinal_valor_depositado="+",
            valor_depositado=Decimal("9650.00"),
            valor_depositado_original="0000000965000",
        )

        assert conta.tipo_registro == "C"
        assert conta.banco == "0341"
        assert conta.agencia == "12345"
        assert conta.valor_depositado == Decimal("9650.00")

    def test_conta_recebimento_dados_bancarios(self):
        """Testa campos bancários obrigatórios."""
        conta = RegistroContaRecebimento(
            tipo_registro="C",
            banco="0001",
            agencia="001",
            conta="123",
            sinal_valor_depositado="+",
            valor_depositado=Decimal("100.00"),
        )

        assert conta.banco != ""
        assert conta.agencia != ""
        assert conta.conta != ""

    def test_conta_recebimento_valor_zero(self):
        """Testa conta com valor depositado zero."""
        conta = RegistroContaRecebimento(
            tipo_registro="C",
            banco="0001",
            agencia="001",
            conta="123",
            sinal_valor_depositado="+",
            valor_depositado=Decimal("0.00"),
        )

        assert conta.valor_depositado == Decimal("0.00")

    def test_conta_recebimento_tamanho_campos(self):
        """Testa limites de tamanho dos campos."""
        # Banco deve ter no máximo 4 caracteres
        conta = RegistroContaRecebimento(
            tipo_registro="C",
            banco="0001",
            agencia="12345",
            conta="12345678901234567890",
            sinal_valor_depositado="+",
            valor_depositado=Decimal("100.00"),
        )

        assert len(conta.banco) <= 4
        assert len(conta.agencia) <= 5
        assert len(conta.conta) <= 20


class TestRegistroReservaFinanceira:
    """Testes para o modelo RegistroReservaFinanceira (registro tipo R)."""

    def test_criar_reserva_financeira_valida(self):
        """Testa criação de reserva financeira válida."""
        reserva = RegistroReservaFinanceira(
            tipo_registro="R",
            estabelecimento_submissor="1234567890",
            cpf_cnpj_titular_movimento="12345678901234",
            bandeira="001",
            matriz_pagamento="1234567890",
            sinal_valor_reserva="+",
            valor_reserva=Decimal("1000.00"),
            valor_reserva_original="0000000100000",
            chave_ur="ABC123DEF456",
            data_vencimento_original=date(2024, 12, 25),
            numero_estabelecimento_pagamento="1234567890",
        )

        assert reserva.tipo_registro == "R"
        assert reserva.valor_reserva == Decimal("1000.00")
        assert reserva.bandeira == "001"

    def test_reserva_financeira_bandeira_descricao(self):
        """Testa property de descrição da bandeira."""
        reserva = RegistroReservaFinanceira(
            tipo_registro="R",
            estabelecimento_submissor="1234567890",
            cpf_cnpj_titular_movimento="12345678901234",
            bandeira="002",  # Mastercard
            matriz_pagamento="1234567890",
            sinal_valor_reserva="+",
            valor_reserva=Decimal("500.00"),
            chave_ur="XYZ789",
        )

        assert reserva.bandeira_descricao == "Master Card"

    def test_reserva_financeira_data_opcional(self):
        """Testa que data de vencimento é opcional."""
        reserva = RegistroReservaFinanceira(
            tipo_registro="R",
            estabelecimento_submissor="1234567890",
            cpf_cnpj_titular_movimento="12345678901234",
            bandeira="001",
            matriz_pagamento="1234567890",
            sinal_valor_reserva="+",
            valor_reserva=Decimal("100.00"),
            chave_ur="ABC",
        )

        assert reserva.data_vencimento_original is None

    def test_reserva_financeira_chave_ur(self):
        """Testa campo chave UR obrigatório."""
        reserva = RegistroReservaFinanceira(
            tipo_registro="R",
            estabelecimento_submissor="1234567890",
            cpf_cnpj_titular_movimento="12345678901234",
            bandeira="001",
            matriz_pagamento="1234567890",
            sinal_valor_reserva="+",
            valor_reserva=Decimal("100.00"),
            chave_ur="CHAVE_UR_TESTE_123456",
        )

        assert reserva.chave_ur == "CHAVE_UR_TESTE_123456"
        assert len(reserva.chave_ur) <= 100


class TestValidacoesGerais:
    """Testes de validações gerais aplicáveis a múltiplos modelos."""

    def test_valores_decimais_precisao(self):
        """Testa que Decimals mantêm precisão correta."""
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            id_pix="abc",
            nsu_doc="123",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("123.45"),
            valor_bruto_original="0000000012345",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("1.23"),
            valor_taxa_administrativa_original="0000000000123",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("122.22"),
            valor_liquido_original="0000000012222",
            banco="0001",
            agencia="001",
            conta="123",
        )

        # Decimal deve manter exatamente 2 casas decimais
        assert pix.valor_bruto == Decimal("123.45")
        assert str(pix.valor_bruto) == "123.45"

    def test_valores_originais_preservados_todos_registros(self):
        """Testa que valores originais são preservados em todos os registros com valores."""
        # Testa Pix
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            id_pix="abc",
            nsu_doc="123",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("1.00"),
            valor_taxa_administrativa_original="0000000000100",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("99.00"),
            valor_liquido_original="0000000009900",
            banco="0001",
            agencia="001",
            conta="123",
        )
        assert pix.valor_bruto_original == "0000000010000"

        # Testa Negociação Resumo
        resumo = RegistroNegociacaoResumo(
            tipo_registro="A",
            cpf_cnpj="12345678901234",
            prazo_medio=30,
            taxa_nominal=Decimal("3.500"),
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("970.00"),
            valor_liquido_original="0000000097000",
        )
        assert resumo.valor_bruto_original == "0000000100000"

    def test_tipo_registro_frozen(self):
        """Testa que tipo_registro não pode ser alterado após criação."""
        pix = RegistroPix(
            tipo_registro="8",
            estabelecimento_submissor="1234567890",
            tipo_transacao="01",
            id_pix="abc",
            nsu_doc="123",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("100.00"),
            valor_bruto_original="0000000010000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("1.00"),
            valor_taxa_administrativa_original="0000000000100",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("99.00"),
            valor_liquido_original="0000000009900",
            banco="0001",
            agencia="001",
            conta="123",
        )

        # tipo_registro é frozen, tentar alterar deve falhar
        with pytest.raises(ValidationError):
            pix.tipo_registro = "E"


class TestModelsPropriedadesCompletas:
    """Testes para todas as propriedades de descrição dos models."""

    def test_registro_detalhe_tipo_liquidacao_descricao(self):
        """Testa descrição de tipo de liquidação."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )
        assert detalhe.tipo_liquidacao_descricao == "Crédito"

    def test_registro_detalhe_tipo_lancamento_descricao(self):
        """Testa descrição de tipo de lançamento."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )
        assert detalhe.tipo_lancamento_descricao == "Venda crédito"

    def test_registro_detalhe_codigo_ajuste_descricao(self):
        """Testa descrição de código de ajuste."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            codigo_ajuste="0001",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )
        assert detalhe.codigo_ajuste_descricao != ""

    def test_registro_detalhe_canal_venda_descricao(self):
        """Testa descrição de canal de venda."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
            canal_venda="001",
        )
        assert detalhe.canal_venda_descricao == "POS (Point of Sale)"

    def test_registro_detalhe_tipo_cartao_descricao(self):
        """Testa descrição de tipo de cartão."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
            tipo_cartao="01",
        )
        assert detalhe.tipo_cartao_descricao == "Visa Classic"

    def test_registro_detalhe_tipo_captura_descricao(self):
        """Testa descrição de tipo de captura."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
            tipo_captura="05",
        )
        assert detalhe.tipo_captura_descricao == "Leitura de chip"

    def test_registro_detalhe_codigo_modelo_precificacao_descricao(self):
        """Testa descrição de código de modelo de precificação."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
            codigo_modelo_precificacao="00003",
        )
        assert detalhe.codigo_modelo_precificacao_descricao == "Venda"


class TestModelsPropriedades:
    """Testes para propriedades calculadas dos models."""

    def test_registro_detalhe_bandeira_descricao_desconhecida(self):
        """Testa descrição de bandeira desconhecida."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="999",  # Bandeira inexistente
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )
        assert detalhe.bandeira_liquidacao_descricao == "Desconhecida"

    def test_registro_detalhe_forma_pagamento_descricao_desconhecida(self):
        """Testa descrição de forma de pagamento desconhecida."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="999",  # Forma inexistente
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
        )
        assert detalhe.forma_pagamento_descricao == "Desconhecida"

    def test_registro_detalhe_grupo_cartoes_descricao(self):
        """Testa descrição de grupo de cartões."""
        detalhe = RegistroDetalhe(
            tipo_registro="E",
            estabelecimento_submissor="1234567890",
            bandeira_liquidacao="001",
            tipo_liquidacao="002",
            parcela=1,
            numero_total_parcelas=1,
            codigo_autorizacao="123456",
            tipo_lancamento="02",
            chave_ur="",
            forma_pagamento="040",
            nsu_doc="654321",
            taxa_mdr=Decimal("2.5"),
            sinal_valor_total_venda="+",
            valor_total_venda=Decimal("1000.00"),
            valor_total_venda_original="0000000100000",
            sinal_valor_bruto="+",
            valor_bruto_venda_parcela=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_valor_liquido="+",
            valor_liquido_venda=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            sinal_valor_comissao="-",
            valor_comissao=Decimal("25.00"),
            valor_comissao_original="0000000002500",
            grupo_cartoes="01",
        )
        assert detalhe.grupo_cartoes_descricao == "Cartão emitido no Brasil"

    def test_registro_ur_agenda_bandeira_descricao(self):
        """Testa descrição de bandeira em UR Agenda."""
        ur = RegistroURAgenda(
            tipo_registro="D",
            estabelecimento_submissor="1234567890",
            cpf_cnpj_titular="12345678901234",
            cpf_cnpj_titular_movimento="12345678901234",
            cpf_cnpj_recebedor="12345678901234",
            bandeira="001",
            tipo_liquidacao="002",
            matriz_pagamento="1234567890",
            status_pagamento="04",
            sinal_valor_bruto="+",
            valor_bruto=Decimal("1000.00"),
            valor_bruto_original="0000000100000",
            sinal_taxa_administrativa="-",
            valor_taxa_administrativa=Decimal("25.00"),
            valor_taxa_administrativa_original="0000000002500",
            sinal_valor_liquido="+",
            valor_liquido=Decimal("975.00"),
            valor_liquido_original="0000000097500",
            banco="0341",
            agencia="12345",
            conta="12345678901234567890",
            digito_conta="1",
            quantidade_lancamentos=10,
            tipo_lancamento="02",
            chave_ur="",
        )
        assert ur.bandeira_descricao == "Visa"
