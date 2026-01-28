import pytest

# Linhas de exemplo baseadas no layout Cielo EDI v15.14.1
# Posições são fixas conforme manual


def criar_header(opcao_extrato: str = "04") -> str:
    """Helper para criar linha de header com tipo de arquivo específico."""
    linha = "0"  # Tipo registro
    linha += "1234567890"  # Estabelecimento matriz (2-11)
    linha += "20241218"  # Data processamento AAAAMMDD (12-19)
    linha += "20241201"  # Período inicial (20-27)
    linha += "20241231"  # Período final (28-35)
    linha += "0000001"  # Sequência (36-42)
    linha += "CIELO"  # Empresa adquirente (43-47)
    linha += opcao_extrato  # Opção extrato (48-49)
    linha += "N"  # Transmissão (50)
    linha += " " * 20  # Caixa postal (51-70)
    linha += "151"  # Versão layout (71-73)
    linha += " " * 177  # Resto do registro
    return linha


@pytest.fixture
def linha_header():
    """Linha de exemplo do Registro 0 (Header) - CIELO04."""
    return criar_header("04")


@pytest.fixture
def linha_ur_agenda():
    """Linha de exemplo do Registro D (UR Agenda)."""
    linha = "D"  # Tipo registro
    linha += "1234567890"  # EC submissor (2-11)
    linha += "12345678901234"  # CPF/CNPJ titular (12-25)
    linha += "12345678901234"  # CPF/CNPJ titular mov (26-39)
    linha += "12345678901234"  # CPF/CNPJ recebedor (40-53)
    linha += "001"  # Bandeira (54-56) - Visa
    linha += "002"  # Tipo liquidação (57-59) - Crédito
    linha += "1234567890"  # Matriz pagamento (60-69)
    linha += "04"  # Status pagamento (70-71) - Pago
    linha += "+"  # Sinal valor bruto (72)
    linha += "0000000100000"  # Valor bruto 1000.00 (73-85)
    linha += "-"  # Sinal taxa (86)
    linha += "0000000002500"  # Taxa 25.00 (87-99)
    linha += "+"  # Sinal valor líquido (100)
    linha += "0000000097500"  # Valor líquido 975.00 (101-113)
    linha += "0341"  # Banco (114-117)
    linha += "12345"  # Agência (118-122)
    linha += "12345678901234567890"  # Conta (123-142)
    linha += "1"  # Dígito (143)
    linha += "000010"  # Qtd lançamentos (144-149)
    linha += "02"  # Tipo lançamento (150-151) - Venda crédito
    linha += " " * 100  # Chave UR (152-251)
    linha += " " * 16  # Campos adicionais
    linha += "18122024"  # Data pagamento DDMMAAAA (268-275)
    linha += "17122024"  # Data envio banco (276-283)
    linha += "15122024"  # Data vencimento original (284-291)
    linha += " " * 109  # Resto
    return linha


@pytest.fixture
def linha_detalhe():
    """Linha de exemplo do Registro E (Detalhe)."""
    linha = "E"  # Tipo registro
    linha += "1234567890"  # EC submissor (2-11)
    linha += "001"  # Bandeira liquidação (12-14) - Visa
    linha += "002"  # Tipo liquidação (15-17) - Crédito
    linha += "01"  # Parcela (18-19)
    linha += "03"  # Total parcelas (20-21)
    linha += "123456"  # Código autorização (22-27)
    linha += "02"  # Tipo lançamento (28-29) - Venda crédito
    linha += " " * 100  # Chave UR (30-129)
    linha += " " * 22  # Código transação (130-151)
    linha += "0000"  # Código ajuste (152-155)
    linha += "040"  # Forma pagamento (156-158) - Visa crédito à vista
    linha += " " * 7  # Indicativos (159-165)
    linha += "123456"  # BIN cartão (166-171)
    linha += "7890"  # Últimos 4 dígitos (172-175)
    linha += "654321"  # NSU (176-181)
    linha += " " * 10  # Nota fiscal (182-191)
    linha += " " * 20  # TID (192-211)
    linha += " " * 20  # Código pedido (212-231)
    linha += "02500"  # Taxa MDR 2.5% (232-236)
    linha += "00000"  # Taxa receb auto (237-241)
    linha += "00000"  # Taxa venda (242-246)
    linha += "+"  # Sinal valor total venda (247)
    linha += "0000000300000"  # Valor total venda 3000.00 (248-260)
    linha += "+"  # Sinal valor bruto (261)
    linha += "0000000100000"  # Valor bruto parcela 1000.00 (262-274)
    linha += "+"  # Sinal valor líquido (275)
    linha += "0000000097500"  # Valor líquido 975.00 (276-288)
    linha += "-"  # Sinal comissão (289)
    linha += "0000000002500"  # Comissão 25.00 (290-302)
    linha += " " * 168  # Campos intermediários
    linha += "143025"  # Hora transação 14:30:25 (471-476)
    linha += "01"  # Grupo cartões (477-478)
    linha += " " * 282  # Resto do registro
    return linha


@pytest.fixture
def linha_trailer():
    """Linha de exemplo do Registro 9 (Trailer)."""
    linha = "9"  # Tipo registro
    linha += "00000000100"  # Total registros (2-12)
    linha += "+"  # Sinal valor líquido (13)
    linha += "00000000009750000"  # Valor líquido soma 97500.00 (14-30)
    linha += "00000000050"  # Qtd registro E (31-41)
    linha += "+"  # Sinal valor bruto (42)
    linha += "00000000010000000"  # Valor bruto soma 100000.00 (43-59)
    linha += "+"  # Sinal valor cedido (60)
    linha += "00000000000000000"  # Valor cedido (61-77)
    linha += "+"  # Sinal valor gravame (78)
    linha += "00000000000000000"  # Valor gravame (79-95)
    linha += " " * 155  # Resto
    return linha


@pytest.fixture
def arquivo_edi_completo(linha_header, linha_ur_agenda, linha_detalhe, linha_trailer):
    """Arquivo EDI completo com todos os tipos de registro."""
    return "\n".join([
        linha_header,
        linha_ur_agenda,
        linha_detalhe,
        linha_trailer,
    ])


@pytest.fixture
def linha_pix():
    """Linha de exemplo do Registro 8 (Transação Pix)."""
    linha = "8"  # Tipo registro (1)
    linha += "1234567890"  # EC submissor (2-11)
    linha += "01"  # Tipo transação (12-13)
    linha += "241218"  # Data transação AAMMDD (14-19)
    linha += "143025"  # Hora transação HHMMSS (20-25)
    linha += "123e4567e89b12d3a456426614174000abcd"  # ID Pix (26-61) - 36 chars
    linha += "654321"  # NSU (62-67)
    linha += "241218"  # Data pagamento AAMMDD (68-73)
    linha += "+"  # Sinal valor bruto (74)
    linha += "0000000050000"  # Valor bruto 500.00 (75-87)
    linha += "-"  # Sinal taxa (88)
    linha += "0000000001000"  # Taxa 10.00 (89-101)
    linha += "+"  # Sinal valor líquido (102)
    linha += "0000000049000"  # Valor líquido 490.00 (103-115)
    linha += "0341"  # Banco (116-119)
    linha += "12345"  # Agência (120-124)
    linha += "12345678901234567890"  # Conta (125-144)
    linha += "241218"  # Data captura AAMMDD (145-150)
    linha += "00100"  # Taxa administrativa 1.00% (151-155)
    linha += "0100"  # Tarifa administrativa 1.00 (156-159)
    linha += "02"  # Canal venda (160-161)
    linha += "12345678"  # Número lógico terminal (162-169)
    linha += " " * 70  # Campos intermediários (170-239)
    linha += "123e4567e89b12d3a456426614174111wxyz"  # TX ID (240-275) - 36 chars
    linha += " " * 125  # Resto até 400
    return linha


@pytest.fixture
def linha_negociacao_resumo():
    """Linha de exemplo do Registro A (Negociação Resumo)."""
    linha = "A"  # Tipo registro (1)
    linha += "241218"  # Data negociação AAMMDD (2-7)
    linha += "241220"  # Data pagamento AAMMDD (8-13)
    linha += "12345678901234"  # CPF/CNPJ (14-27)
    linha += "030"  # Prazo médio dias (28-30)
    linha += "03500"  # Taxa nominal 3.5% (31-35)
    linha += "+"  # Sinal valor bruto (36)
    linha += "0000001000000"  # Valor bruto 10000.00 (37-49)
    linha += "+"  # Sinal valor líquido (50)
    linha += "0000000965000"  # Valor líquido 9650.00 (51-63)
    linha += "12345678901234567890"  # Número negociação (64-83)
    linha += "001"  # Forma pagamento (84-86)
    linha += "03650"  # Taxa efetiva 3.65% (87-91)
    linha += " " * 159  # Resto até 250
    return linha


@pytest.fixture
def linha_negociacao_detalhe():
    """Linha de exemplo do Registro B (Negociação Detalhe)."""
    linha = "B"  # Tipo registro (1)
    linha += "241218"  # Data negociação AAMMDD (2-7)
    linha += "241225"  # Data vencimento original AAMMDD (8-13)
    linha += "12345678901234"  # CPF/CNPJ (14-27)
    linha += "001"  # Bandeira (28-30) - Visa
    linha += "002"  # Tipo liquidação (31-33) - Crédito
    linha += "+"  # Sinal valor bruto (34)
    linha += "0000000500000"  # Valor bruto 5000.00 (35-47)
    linha += "+"  # Sinal valor líquido (48)
    linha += "0000000482500"  # Valor líquido 4825.00 (49-61)
    linha += "03500"  # Taxa efetiva 3.5% (62-66)
    linha += "Banco Exemplo" + " " * 37  # Instituição financeira (67-116)
    linha += "1234567890"  # Número estabelecimento (117-126)
    linha += "-"  # Sinal valor desconto (127)
    linha += "0000000017500"  # Valor desconto 175.00 (128-140)
    linha += " " * 110  # Resto até 250
    return linha


@pytest.fixture
def linha_conta_recebimento():
    """Linha de exemplo do Registro C (Conta Recebimento)."""
    linha = "C"  # Tipo registro
    linha += "0341"  # Banco (2-5)
    linha += "12345"  # Agência (6-10)
    linha += "12345678901234567890"  # Conta (11-30)
    linha += "+"  # Sinal valor depositado (31)
    linha += "0000000965000"  # Valor depositado 9650.00 (32-44)
    linha += " " * 206  # Resto
    return linha


@pytest.fixture
def linha_reserva_financeira():
    """Linha de exemplo do Registro R (Reserva Financeira)."""
    linha = "R"  # Tipo registro
    linha += "1234567890"  # EC submissor (2-11)
    linha += "12345678901234"  # CPF/CNPJ titular mov (12-25)
    linha += "001"  # Bandeira (26-28) - Visa
    linha += "1234567890"  # Matriz pagamento (29-38)
    linha += "+"  # Sinal valor reserva (39)
    linha += "0000000100000"  # Valor reserva 1000.00 (40-52)
    linha += " " * 100  # Chave UR (53-152)
    linha += "25122024"  # Data vencimento original DDMMAAAA (153-160)
    linha += "1234567890"  # Número EC pagamento (161-170)
    linha += " " * 80  # Resto
    return linha


@pytest.fixture
def arquivo_edi_minimo():
    """Arquivo EDI mínimo válido (apenas header e trailer)."""
    header = "0" + "1234567890" + "20241218" + "20241201" + "20241231" + "0000001" + "CIELO" + "04" + "N" + " " * 201
    trailer = "9" + "00000000002" + "+" + "00000000000000000" + "00000000000" + "+" + "00000000000000000" + " " * 173
    return "\n".join([header, trailer])


# Arquivos completos por tipo


@pytest.fixture
def arquivo_cielo03():
    """Arquivo CIELO03 completo (Captura/Previsão)."""
    header = criar_header("03")
    ur = "D" + "1234567890" + "12345678901234" * 3 + "001" + "002" + "1234567890" + "01"
    ur += "+" + "0000000100000" + "-" + "0000000002500" + "+" + "0000000097500"
    ur += "0341" + "12345" + "12345678901234567890" + "1" + "000010" + "02" + " " * 100
    ur += " " * 16 + "18122024" + "17122024" + "15122024" + " " * 109

    detalhe = "E" + "1234567890" + "001" + "002" + "01" + "01" + "123456" + "02" + " " * 100
    detalhe += " " * 22 + "0000" + "040" + " " * 7 + "123456" + "7890" + "654321" + " " * 10
    detalhe += " " * 40 + "02500" + "00000" + "00000" + "+" + "0000000100000"
    detalhe += "+" + "0000000100000" + "+" + "0000000097500" + "-" + "0000000002500"
    detalhe += " " * 168 + "143025" + "01" + " " * 282

    trailer = "9" + "00000000004" + "+" + "00000000009750000" + "00000000001" + "+" + "00000000010000000"
    trailer += "+" + "00000000000000000" + "+" + "00000000000000000" + " " * 155

    return "\n".join([header, ur, detalhe, trailer])


@pytest.fixture
def arquivo_cielo04(arquivo_edi_completo):
    """Arquivo CIELO04 completo (Liquidação/Pagamento) - usa fixture existente."""
    return arquivo_edi_completo


@pytest.fixture
def arquivo_cielo09():
    """Arquivo CIELO09 completo (Saldo em Aberto)."""
    header = criar_header("09")
    ur = "D" + "1234567890" + "12345678901234" * 3 + "001" + "002" + "1234567890" + "01"
    ur += "+" + "0000000100000" + "-" + "0000000002500" + "+" + "0000000097500"
    ur += "0341" + "12345" + "12345678901234567890" + "1" + "000010" + "02" + " " * 100
    ur += " " * 16 + "00000000" + "00000000" + "15122024" + " " * 109

    detalhe = "E" + "1234567890" + "001" + "002" + "01" + "03" + "123456" + "02" + " " * 100
    detalhe += " " * 22 + "0000" + "040" + " " * 7 + "123456" + "7890" + "654321" + " " * 10
    detalhe += " " * 40 + "02500" + "00000" + "00000" + "+" + "0000000300000"
    detalhe += "+" + "0000000100000" + "+" + "0000000097500" + "-" + "0000000002500"
    detalhe += " " * 168 + "143025" + "01" + " " * 282

    trailer = "9" + "00000000004" + "+" + "00000000009750000" + "00000000001" + "+" + "00000000010000000"
    trailer += "+" + "00000000000000000" + "+" + "00000000000000000" + " " * 155

    return "\n".join([header, ur, detalhe, trailer])


@pytest.fixture
def arquivo_cielo15(linha_negociacao_resumo, linha_negociacao_detalhe,
                     linha_conta_recebimento, linha_reserva_financeira):
    """Arquivo CIELO15 completo (Negociação de Recebíveis)."""
    header = criar_header("15")
    trailer = "9" + "00000000006" + "+" + "00000000096500000" + "00000000000" + "+" + "00000000100000000"
    trailer += "+" + "00000000010000000" + "+" + "00000000010000000" + " " * 155

    return "\n".join([
        header,
        linha_negociacao_resumo,
        linha_negociacao_detalhe,
        linha_conta_recebimento,
        linha_reserva_financeira,
        trailer,
    ])


@pytest.fixture
def arquivo_cielo16(linha_pix):
    """Arquivo CIELO16 completo (Pix)."""
    header = criar_header("16")
    trailer = "9" + "00000000003" + "+" + "00000000049000000" + "00000000000" + "+" + "00000000050000000"
    trailer += "+" + "00000000000000000" + "+" + "00000000000000000" + " " * 155

    return "\n".join([header, linha_pix, trailer])
