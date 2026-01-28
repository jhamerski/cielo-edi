# Script PowerShell para executar testes no Windows
# Equivalente ao Makefile para ambientes Windows
# Uso: .\test.ps1 <comando> [argumentos]

param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$File = "",

    [Parameter(Position=2)]
    [string]$Class = "",

    [Parameter(Position=3)]
    [string]$Func = ""
)

$PYTHON = "python"
$PYTEST = "pytest"
$TEST_DIR = "tests"
$SRC_DIR = "src"

function Show-Help {
    Write-Host ""
    Write-Host "Cielo EDI - Comandos de Teste (Windows)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\test.ps1 <comando> [argumentos]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Testes:" -ForegroundColor Green
    Write-Host "  .\test.ps1 all              - Executa todos os testes"
    Write-Host "  .\test.ps1 verbose          - Testes com saída detalhada"
    Write-Host "  .\test.ps1 unit             - Apenas testes unitários"
    Write-Host "  .\test.ps1 integration      - Apenas testes de integração"
    Write-Host "  .\test.ps1 cov              - Testes com cobertura"
    Write-Host "  .\test.ps1 cov-html         - Relatório HTML de cobertura"
    Write-Host ""
    Write-Host "Testes específicos:" -ForegroundColor Green
    Write-Host "  .\test.ps1 file tests/test_models.py"
    Write-Host "  .\test.ps1 class tests/test_models.py TestRegistroHeader"
    Write-Host "  .\test.ps1 func tests/test_models.py TestRegistroHeader test_criar_header_valido"
    Write-Host ""
    Write-Host "Atalhos rápidos:" -ForegroundColor Green
    Write-Host "  .\test.ps1 models           - Testa test_models.py"
    Write-Host "  .\test.ps1 parsers          - Testa test_parser.py"
    Write-Host "  .\test.ps1 cli              - Testa test_cli.py"
    Write-Host "  .\test.ps1 x                - Para no primeiro erro"
    Write-Host "  .\test.ps1 failed           - Apenas testes que falharam"
    Write-Host ""
    Write-Host "Qualidade:" -ForegroundColor Green
    Write-Host "  .\test.ps1 lint             - Executa linter"
    Write-Host "  .\test.ps1 format           - Formata código"
    Write-Host "  .\test.ps1 typecheck        - Verifica tipos"
    Write-Host ""
    Write-Host "Outros:" -ForegroundColor Green
    Write-Host "  .\test.ps1 clean            - Limpa arquivos temporários"
    Write-Host "  .\test.ps1 install          - Instala em modo dev"
    Write-Host ""
}

function Run-AllTests {
    & $PYTEST $TEST_DIR
}

function Run-VerboseTests {
    & $PYTEST $TEST_DIR -vv
}

function Run-UnitTests {
    & $PYTEST $TEST_DIR -m unit -v
}

function Run-IntegrationTests {
    & $PYTEST $TEST_DIR -m integration -v
}

function Run-TestsWithCoverage {
    & $PYTEST $TEST_DIR --cov=cielo_edi --cov-report=term-missing
}

function Run-CoverageHtml {
    & $PYTEST $TEST_DIR --cov=cielo_edi --cov-report=html
    Write-Host ""
    Write-Host "Relatório gerado em: htmlcov\index.html" -ForegroundColor Green
    Write-Host "Abrindo no navegador..." -ForegroundColor Yellow
    Start-Process "htmlcov\index.html"
}

function Run-FileTests {
    if ([string]::IsNullOrEmpty($File)) {
        Write-Host "Erro: Especifique o arquivo" -ForegroundColor Red
        Write-Host "Exemplo: .\test.ps1 file tests/test_models.py" -ForegroundColor Yellow
        exit 1
    }
    & $PYTEST $File -v
}

function Run-ClassTests {
    if ([string]::IsNullOrEmpty($File) -or [string]::IsNullOrEmpty($Class)) {
        Write-Host "Erro: Especifique arquivo e classe" -ForegroundColor Red
        Write-Host "Exemplo: .\test.ps1 class tests/test_models.py TestRegistroHeader" -ForegroundColor Yellow
        exit 1
    }
    & $PYTEST "${File}::${Class}" -v
}

function Run-FuncTest {
    if ([string]::IsNullOrEmpty($File) -or [string]::IsNullOrEmpty($Class) -or [string]::IsNullOrEmpty($Func)) {
        Write-Host "Erro: Especifique arquivo, classe e função" -ForegroundColor Red
        Write-Host "Exemplo: .\test.ps1 func tests/test_models.py TestRegistroHeader test_criar_header_valido" -ForegroundColor Yellow
        exit 1
    }
    & $PYTEST "${File}::${Class}::${Func}" -vv
}

function Run-ModelsTests {
    & $PYTEST "$TEST_DIR\test_models.py" -v
}

function Run-ParsersTests {
    & $PYTEST "$TEST_DIR\test_parser.py" -v
}

function Run-CliTests {
    & $PYTEST "$TEST_DIR\test_cli.py" -v
}

function Run-TestsStopOnError {
    & $PYTEST $TEST_DIR -x
}

function Run-FailedTests {
    & $PYTEST $TEST_DIR --lf -v
}

function Run-Lint {
    & ruff check $SRC_DIR $TEST_DIR
}

function Run-Format {
    & ruff format $SRC_DIR $TEST_DIR
    & ruff check --fix $SRC_DIR $TEST_DIR
}

function Run-TypeCheck {
    & mypy $SRC_DIR
}

function Clean-Project {
    Write-Host "Limpando arquivos temporários..." -ForegroundColor Yellow

    Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter ".pytest_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter ".mypy_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter ".ruff_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter "htmlcov" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter ".coverage" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

    Write-Host "Limpeza concluída!" -ForegroundColor Green
}

function Install-Dev {
    & pip install -e ".[dev]"
}

# Processa o comando
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "all" { Run-AllTests }
    "test" { Run-AllTests }
    "verbose" { Run-VerboseTests }
    "v" { Run-VerboseTests }
    "unit" { Run-UnitTests }
    "integration" { Run-IntegrationTests }
    "cov" { Run-TestsWithCoverage }
    "coverage" { Run-TestsWithCoverage }
    "cov-html" { Run-CoverageHtml }
    "file" { Run-FileTests }
    "class" { Run-ClassTests }
    "func" { Run-FuncTest }
    "function" { Run-FuncTest }
    "models" { Run-ModelsTests }
    "parsers" { Run-ParsersTests }
    "cli" { Run-CliTests }
    "x" { Run-TestsStopOnError }
    "failed" { Run-FailedTests }
    "lint" { Run-Lint }
    "format" { Run-Format }
    "typecheck" { Run-TypeCheck }
    "clean" { Clean-Project }
    "install" { Install-Dev }
    default {
        Write-Host "Comando desconhecido: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}