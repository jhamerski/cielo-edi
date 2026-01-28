# Cielo EDI Parser

[![PyPI version](https://badge.fury.io/py/cielo-edi.svg)](https://pypi.org/project/cielo-edi/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Parser para arquivos Cielo EDI (Extrato Eletrônico). Converte CIELO03/04/09/15/16 para JSON ou CSV.

## Features

- Suporta CIELO03/04/09/15/16
- Validação com Pydantic v2
- Streaming para arquivos grandes
- Exportação JSON e CSV
- CLI incluída

## Instalação

```bash
pip install cielo-edi
```

**Requisitos:** Python 3.9+, Pydantic 2.5+ e pytest (para testes)

## Uso

```python
from cielo_edi import CieloEDIParser, JSONExporter, CSVExporter

parser = CieloEDIParser()
resultado = parser.processar("CIELO04_20241218.txt")

# Acessar dados
print(f"Tipo: {resultado.tipo_arquivo_descricao}")
print(f"Valor: R$ {resultado.estatisticas.valor_liquido_total:,.2f}")

for detalhe in resultado.detalhes:
    print(f"{detalhe.nsu_doc} | R$ {detalhe.valor_liquido_venda:,.2f}")

# Exportar JSON
exporter = JSONExporter(indent=2)
exporter.exportar_arquivo(resultado, "saida.json")

# Exportar CSV
CSVExporter(delimiter=";").exportar_todos(resultado, "./csv/")

# Streaming (arquivos grandes)
for registro in parser.processar_streaming("arquivo_10GB.txt"):
    processar(registro)
```

### CLI

```bash
cielo-edi arquivo.txt -o resultado.json
cielo-edi arquivo.txt --formato csv --diretorio ./saida
cielo-edi arquivo.txt --info
```

## Tipos de Arquivo

| Código | Descrição |
|--------|-----------|
| CIELO03 | Captura/Previsão |
| CIELO04 | Liquidação/Pagamento |
| CIELO09 | Saldo em Aberto |
| CIELO15 | Negociação de Recebíveis |
| CIELO16 | Pix |

## Tipos de Registro

| Código | Descrição |
|--------|-----------|
| 0 | Header |
| D | UR Agenda (Unidade de Recebimento) |
| E | Detalhe do Lançamento |
| 8 | Transação Pix |
| A | Resumo de Negociação |
| B | Detalhe de Negociação |
| C | Conta de Recebimento |
| R | Reserva Financeira |
| 9 | Trailer |

## Links

- [Repositório](https://github.com/jhamerski/cielo-edi)
- [Issues](https://github.com/jhamerski/cielo-edi/issues)

## Licença

MIT - Esta biblioteca não é oficial e não possui vínculo com a Cielo.