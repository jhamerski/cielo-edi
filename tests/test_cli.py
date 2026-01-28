import pytest
import tempfile
from pathlib import Path
import sys

from cielo_edi.cli import criar_parser_args, exibir_info, main


class TestCriarParserArgs:
    """Testes para função criar_parser_args."""

    def test_parser_basico(self):
        """Testa criação do parser de argumentos."""
        parser = criar_parser_args()

        assert parser is not None
        assert parser.prog == "cielo-edi"

    def test_parser_help(self):
        """Testa que --help funciona."""
        parser = criar_parser_args()

        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_parser_versao(self):
        """Testa que --version funciona."""
        parser = criar_parser_args()

        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parser_arquivo_requerido(self):
        """Testa que arquivo é requerido."""
        parser = criar_parser_args()

        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_argumento_arquivo(self):
        """Testa argumento de arquivo."""
        parser = criar_parser_args()
        args = parser.parse_args(["arquivo.txt"])

        assert args.arquivo == Path("arquivo.txt")

    def test_parser_opcao_output(self):
        """Testa opção -o/--output."""
        parser = criar_parser_args()
        args = parser.parse_args(["arquivo.txt", "-o", "resultado.json"])

        assert args.output == Path("resultado.json")

    def test_parser_opcao_diretorio(self):
        """Testa opção -d/--diretorio."""
        parser = criar_parser_args()
        args = parser.parse_args(["arquivo.txt", "-d", "saida"])

        assert args.diretorio == Path("saida")

    def test_parser_opcao_formato(self):
        """Testa opção -f/--formato."""
        parser = criar_parser_args()
        args = parser.parse_args(["arquivo.txt", "-f", "csv"])

        assert args.formato == "csv"

    def test_parser_opcao_encoding(self):
        """Testa opção -e/--encoding."""
        parser = criar_parser_args()
        args = parser.parse_args(["arquivo.txt", "-e", "utf-8"])

        assert args.encoding == "utf-8"

    def test_parser_opcao_verbose(self):
        """Testa opção -v/--verbose."""
        parser = criar_parser_args()
        args = parser.parse_args(["arquivo.txt", "-v"])

        assert args.verbose is True


class TestExibirInfo:
    """Testes para função exibir_info."""

    def test_exibir_info_basico(self, arquivo_cielo04, capsys):
        """Testa exibição básica de informações."""
        from cielo_edi.parser import CieloEDIParser

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo04)

        exibir_info(resultado)

        captured = capsys.readouterr()
        assert "CIELO04" in captured.out or "04" in captured.out

    def test_exibir_info_com_pix(self, arquivo_cielo16, capsys):
        """Testa exibição de informações com registro Pix."""
        from cielo_edi.parser import CieloEDIParser

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo16)

        exibir_info(resultado)

        captured = capsys.readouterr()
        assert "Pix" in captured.out or "16" in captured.out

    def test_exibir_info_com_negociacao(self, arquivo_cielo15, capsys):
        """Testa exibição de informações com negociação."""
        from cielo_edi.parser import CieloEDIParser

        parser = CieloEDIParser()
        resultado = parser.processar_string(arquivo_cielo15)

        exibir_info(resultado)

        captured = capsys.readouterr()
        assert "15" in captured.out or "Negociação" in captured.out


class TestMainFunction:
    """Testes para função main do CLI."""

    def test_main_arquivo_inexistente(self, monkeypatch):
        """Testa comportamento com arquivo inexistente."""
        monkeypatch.setattr(sys, "argv", ["cielo-edi", "arquivo_nao_existe.txt"])

        exit_code = main()
        assert exit_code == 1

    def test_main_com_arquivo_valido(self, arquivo_cielo04, monkeypatch):
        """Testa execução com arquivo válido."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path])

            # Main deve executar sem erros
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        finally:
            Path(temp_path).unlink()

    def test_main_output_json(self, arquivo_cielo04, monkeypatch):
        """Testa output em formato JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        output_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        output_path = output_file.name
        output_file.close()

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-o", output_path])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # Verifica que arquivo JSON foi criado
            assert Path(output_path).exists()
            content = Path(output_path).read_text(encoding="utf-8")
            assert len(content) > 0
        finally:
            Path(temp_path).unlink()
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_main_output_csv(self, arquivo_cielo04, monkeypatch):
        """Testa output em formato CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        output_dir = tempfile.mkdtemp()

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-f", "csv", "-d", output_dir])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # Verifica que arquivos CSV foram criados no diretório
            csv_files = list(Path(output_dir).glob("*.csv"))
            assert len(csv_files) > 0
        finally:
            Path(temp_path).unlink()
            # Limpa arquivos CSV criados
            for csv_file in Path(output_dir).glob("*.csv"):
                csv_file.unlink()
            Path(output_dir).rmdir()

    def test_main_encoding_customizado(self, arquivo_cielo04, monkeypatch):
        """Testa uso de encoding customizado."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-e", "utf-8"])

            try:
                main()
            except SystemExit as e:
                # Deve executar sem erro
                assert e.code == 0 or e.code is None
        finally:
            Path(temp_path).unlink()

    def test_main_verbose(self, arquivo_cielo04, monkeypatch, capsys):
        """Testa modo verbose."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-v"])

            try:
                main()
            except SystemExit:
                pass

            captured = capsys.readouterr()
            # Em modo verbose deve exibir mais informações
            assert len(captured.out) > 0 or len(captured.err) > 0
        finally:
            Path(temp_path).unlink()


class TestIntegracaoCLI:
    """Testes de integração do CLI com diferentes tipos de arquivo."""

    def test_cli_arquivo_cielo03(self, arquivo_cielo03, monkeypatch):
        """Testa CLI com arquivo CIELO03."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo03)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
        finally:
            Path(temp_path).unlink()

    def test_cli_arquivo_cielo09(self, arquivo_cielo09, monkeypatch):
        """Testa CLI com arquivo CIELO09."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo09)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
        finally:
            Path(temp_path).unlink()

    def test_cli_arquivo_cielo15(self, arquivo_cielo15, monkeypatch):
        """Testa CLI com arquivo CIELO15."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo15)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
        finally:
            Path(temp_path).unlink()

    def test_cli_arquivo_cielo16(self, arquivo_cielo16, monkeypatch):
        """Testa CLI com arquivo CIELO16."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo16)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
        finally:
            Path(temp_path).unlink()

    def test_cli_multiplos_formatos(self, arquivo_cielo04, monkeypatch):
        """Testa CLI com diferentes formatos de output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        formatos = ["json", "dict", "csv"]

        for formato in formatos:
            try:
                if formato == "csv":
                    output_dir = tempfile.mkdtemp()
                    monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-o", formato, "-d", output_dir])
                else:
                    output_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
                    output_path = output_file.name
                    output_file.close()
                    monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-o", formato, "-d", output_path])

                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0 or e.code is None

                # Limpa arquivos de output
                if formato == "csv":
                    for csv_file in Path(output_dir).glob("*.csv"):
                        csv_file.unlink()
                    Path(output_dir).rmdir()
                else:
                    if Path(output_path).exists():
                        Path(output_path).unlink()
            finally:
                pass

        Path(temp_path).unlink()


class TestCoberturaCLI:
    """Testes adicionais para cobertura completa do CLI."""

    def test_main_modo_info(self, arquivo_cielo04, monkeypatch, capsys):
        """Testa modo --info que apenas exibe informações."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "--info"])

            exit_code = main()
            assert exit_code == 0

            captured = capsys.readouterr()
            assert "RESUMO DO PROCESSAMENTO" in captured.out
        finally:
            Path(temp_path).unlink()

    def test_main_csv_sem_diretorio(self, arquivo_cielo04, monkeypatch):
        """Testa output CSV sem especificar diretório (usa default)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-f", "csv"])

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # Verifica que diretório default foi criado
            default_dir = Path(temp_path).parent / f"{Path(temp_path).stem}_csv"
            assert default_dir.exists()

            # Limpa arquivos criados
            for csv_file in default_dir.glob("*.csv"):
                csv_file.unlink()
            default_dir.rmdir()
        finally:
            Path(temp_path).unlink()

    def test_main_arquivo_com_linhas_invalidas(self, monkeypatch, capsys):
        """Testa processamento de arquivo com linhas inválidas."""
        # Cria arquivo com linhas inválidas
        conteudo = """0123456789020241218202412012024123100000010CIELO04N                    151
LINHA_INVALIDA_QUE_NAO_DEVE_SER_PROCESSADA
900000000001+000000000009750000000000000050+00000000010000000+00000000000000000+00000000000000000                                                                                                                               """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "--info"])

            exit_code = main()
            assert exit_code == 0

            captured = capsys.readouterr()
            # Deve exibir aviso de linhas não processadas
            assert "Linhas não processadas" in captured.out or "processadas" in captured.out.lower()
        finally:
            Path(temp_path).unlink()

    def test_main_json_indent_zero(self, arquivo_cielo04, monkeypatch):
        """Testa output JSON com indent=0 (minificado)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        output_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        output_path = output_file.name
        output_file.close()

        try:
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-o", output_path, "--indent", "0"])

            exit_code = main()
            assert exit_code == 0

            # Verifica que arquivo JSON foi criado
            assert Path(output_path).exists()
            content = Path(output_path).read_text(encoding="utf-8")
            # JSON minificado não deve ter quebras de linha (exceto no final)
            assert len(content.strip().split("\n")) <= 2
        finally:
            Path(temp_path).unlink()
            if Path(output_path).exists():
                Path(output_path).unlink()


class TestCLIExcecoes:
    """Testes para cobertura de tratamento de exceções no CLI."""

    def test_main_excecao_durante_exportacao(self, arquivo_cielo04, monkeypatch):
        """Testa tratamento de exceção durante exportação."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="latin-1") as f:
            f.write(arquivo_cielo04)
            temp_path = f.name

        output_file = Path(tempfile.gettempdir()) / "arquivo_invalido" / "saida.json"

        try:
            # Força erro ao tentar escrever em diretório inexistente
            monkeypatch.setattr(sys, "argv", ["cielo-edi", temp_path, "-o", str(output_file)])

            exit_code = main()
            # Deve retornar código de erro
            assert exit_code == 1
        finally:
            Path(temp_path).unlink()
