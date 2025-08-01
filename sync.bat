@echo off
REM ===============================================================
REM Sincronizador Robusto para o repositorio GitHub
REM Uso: sync.bat [mensagem_commit]
REM 
REM Versao 2.2 - Arquitetura simplificada e robusta
REM ===============================================================

setlocal enabledelayedexpansion

REM *** DEFINICOES GLOBAIS IMEDIATAS ***
REM Estas variaveis sao definidas PRIMEIRO, fora de qualquer bloco condicional
set "DEFAULT_MSG=Update automatico versao 2.2"
set "FALLBACK_MSG=Commit automatico sem mensagem especifica"

REM Limpar variaveis potencialmente contaminadas
set "commit_msg="
set "user_input="
set "CURRENT_BRANCH="
set "LOCAL_COMMIT="
set "REMOTE_COMMIT="
set "continue="

REM Configuracoes do ambiente
set "REPO_DIR=D:\USER\Toni\ITA90\Python\streamlit\party-registration-system"
set "VENV_PATH=.\streamlit\Scripts\activate.bat"
set "TARGET_BRANCH=main"

echo =============================================
echo    Sincronizador GitHub - Versao 2.2
echo =============================================
echo.

REM DEBUG: Verificar se as variaveis globais foram definidas corretamente
echo DEBUG INICIAL: DEFAULT_MSG=[!DEFAULT_MSG!]
echo DEBUG INICIAL: FALLBACK_MSG=[!FALLBACK_MSG!]
echo.

REM Passo 1: Navegar para o diretorio e ativar ambiente virtual
echo [1/8] Acessando diretorio do projeto...
d:
cd /d "%REPO_DIR%" 2>nul
if !errorlevel! neq 0 (
    echo ERRO: Nao foi possivel acessar o diretorio: !REPO_DIR!
    pause
    exit /b 1
)

echo [2/8] Ativando ambiente virtual...
if exist "!VENV_PATH!" (
    call "!VENV_PATH!"
    echo Ambiente virtual ativado com sucesso.
) else (
    echo AVISO: Arquivo do ambiente virtual nao encontrado: !VENV_PATH!
    echo Continuando sem ambiente virtual...
)

REM Passo 2: Verificar se estamos em um repositorio Git valido
echo [3/8] Verificando repositorio Git...
git status >nul 2>&1
if !errorlevel! neq 0 (
    echo ERRO: Este diretorio nao e um repositorio Git valido.
    pause
    exit /b 1
)

REM Verificar branch atual - metodo mais robusto
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "CURRENT_BRANCH=%%i"
if "!CURRENT_BRANCH!"=="" (
    echo AVISO: Nao foi possivel determinar a branch atual. Assumindo main.
    set "CURRENT_BRANCH=main"
)
echo Branch atual: !CURRENT_BRANCH!

if "!CURRENT_BRANCH!" neq "!TARGET_BRANCH!" (
    echo AVISO: Voce esta na branch '!CURRENT_BRANCH!' mas o target e '!TARGET_BRANCH!'
    set /p "continue=Deseja continuar? (s/N): "
    if /i "!continue!" neq "s" (
        echo Operacao cancelada.
        pause
        exit /b 0
    )
)

REM Passo 3: Verificar conectividade com GitHub
echo [4/8] Testando conectividade com GitHub...
git ls-remote origin HEAD >nul 2>&1
if !errorlevel! neq 0 (
    echo ERRO: Nao foi possivel conectar ao repositorio remoto.
    echo Verifique sua conexao com a internet e credenciais do Git.
    pause
    exit /b 1
)
echo Conectividade com GitHub OK.

REM Passo 4: Baixar atualizacoes do repositorio
echo [5/8] Baixando alteracoes do GitHub...
git fetch origin
if !errorlevel! neq 0 (
    echo ERRO: Falha ao fazer fetch do repositorio remoto.
    pause
    exit /b 1
)

git pull origin !CURRENT_BRANCH!
if !errorlevel! neq 0 (
    echo ERRO: Falha no git pull. Pode haver conflitos que precisam ser resolvidos manualmente.
    echo Execute 'git status' para ver os detalhes.
    pause
    exit /b 1
)
echo Pull realizado com sucesso.

REM Passo 5: Verificar e preparar alteracoes locais
echo [6/8] Verificando alteracoes locais...

echo.
echo Status atual do repositorio:
git status --porcelain
echo.

REM Adicionar todas as alteracoes
git add --all
if !errorlevel! neq 0 (
    echo ERRO: Falha ao adicionar arquivos ao staging.
    pause
    exit /b 1
)

REM Verificar se ha mudancas para commit
git diff-index --quiet HEAD
if !errorlevel! equ 0 (
    echo Nenhuma alteracao local para enviar.
    goto :show_logs
) else (
    echo Alteracoes detectadas. Preparando commit...
    echo.
    
    REM *** LOGICA DE MENSAGEM SIMPLIFICADA E ROBUSTA ***
    echo DEBUG PRE-COMMIT: DEFAULT_MSG=[!DEFAULT_MSG!]
    echo DEBUG PRE-COMMIT: FALLBACK_MSG=[!FALLBACK_MSG!]
    
    REM Verificar se foi passado parametro na linha de comando
    if "%~1" neq "" (
        set "commit_msg=%*"
        echo DEBUG: Usando mensagem dos parametros: [!commit_msg!]
        goto :validate_message
    )
    
    REM Se nao ha parametro, pedir input do usuario
    echo Mensagem padrao disponivel: !DEFAULT_MSG!
    echo.
    set /p "user_input=Digite a mensagem do commit (Enter para usar padrao): "
    
    echo DEBUG: Input do usuario capturado: [!user_input!]
    
    REM Decidir qual mensagem usar
    if "!user_input!"=="" (
        set "commit_msg=!DEFAULT_MSG!"
        echo DEBUG: Usuario nao digitou nada, usando DEFAULT_MSG
    ) else (
        set "commit_msg=!user_input!"
        echo DEBUG: Usando input do usuario
    )
    
    :validate_message
    echo DEBUG: Mensagem antes da validacao: [!commit_msg!]
    
    REM Validacao final de seguranca com fallback absoluto
    if "!commit_msg!"=="" (
        echo AVISO: Mensagem ainda vazia, aplicando fallback absoluto...
        set "commit_msg=!FALLBACK_MSG!"
    )
    
    echo DEBUG: Mensagem final para commit: [!commit_msg!]
    echo.
    echo *** COMMIT SERA FEITO COM: "!commit_msg!" ***
    echo.
    pause
    
    REM Realizar commit
    echo [7/8] Fazendo commit: "!commit_msg!"
    git commit -m "!commit_msg!"
    
    REM Verificacao de sucesso mais robusta
    git log -1 --format="%%H" >nul 2>&1
    if !errorlevel! neq 0 (
        echo ERRO: Falha ao fazer commit - nenhum commit foi criado.
        pause
        exit /b 1
    ) else (
        echo Commit realizado com sucesso!
    )
    
    REM Realizar push
    echo [8/8] Enviando alteracoes para o GitHub...
    git push origin !CURRENT_BRANCH!
    if !errorlevel! neq 0 (
        echo ERRO: Falha ao fazer push. Verifique suas credenciais e conectividade.
        echo O commit foi criado localmente mas nao foi enviado ao GitHub.
        pause
        exit /b 1
    )
    
    echo Push realizado com sucesso!
    
    REM Verificar se o push foi realmente efetivado
    echo.
    echo Aguardando 3 segundos e verificando sincronizacao...
    timeout /t 3 /nobreak >nul
    git fetch origin >nul 2>&1
    
    REM Obter hashes para comparacao
    for /f "tokens=*" %%i in ('git log --format^=%%H -n 1') do set "LOCAL_COMMIT=%%i"
    for /f "tokens=*" %%i in ('git log --format^=%%H -n 1 origin/!CURRENT_BRANCH!') do set "REMOTE_COMMIT=%%i"
    
    echo DEBUG: Commit local:  !LOCAL_COMMIT!
    echo DEBUG: Commit remoto: !REMOTE_COMMIT!
    
    if "!LOCAL_COMMIT!"=="!REMOTE_COMMIT!" (
        echo.
        echo *** SUCESSO TOTAL: Sincronizacao confirmada no GitHub! ***
    ) else (
        echo.
        echo *** ATENCAO: Discrepancia detectada entre local e remoto ***
        echo Verifique manualmente no GitHub se o commit apareceu.
    )
)

:show_logs
REM Exibir logs comparativos
echo.
echo =============== RESUMO DOS COMMITS ===============
echo.
echo Ultimos 3 commits LOCAIS:
git log --oneline -3
echo.
echo Ultimos 3 commits REMOTOS:
git log --oneline origin/!CURRENT_BRANCH! -3
echo.
echo ==================================================

echo.
echo VERIFICACAO MANUAL: https://github.com/aespesch/party-registration-system
echo Pressione Ctrl+F5 no browser para refresh completo
echo.

echo Sincronizacao completa!
echo Pressione qualquer tecla para continuar...
pause >nul