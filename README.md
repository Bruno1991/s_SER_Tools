# s_ADB_Tools 2.0 - Canivete Suíço Universal para Android

Canivete suíço completo em Python para qualquer aplicativo Android: detecção e diagnóstico de dispositivos, extração de APKs e App Bundles (Split APKs), descompilação reversa em Java/Gradle (JADX), descompilação de apps Adobe AIR / Flash (ActionScript 3 e assets via JPEXS FFDec), instalação, controle de apps e captura de tela.

---

## ⚡ Principais Recursos do Utilitário Unificado

1. **Gestão de Dispositivos & Emuladores:**
   - Detecta automaticamente dispositivos físicos e emuladores (`emulator-5554`, etc.) via USB e TCP/IP.
   - Diagnóstico em tempo real: modelo, versão do Android, nível de API, fabricante e bateria.
   - Suporte a conexão TCP/IP remota (`adb-tools connect 192.168.x.x:5555`).

2. **Extração Universal de APKs:**
   - Extrai qualquer aplicativo instalado pelo nome do pacote ou busca inteligente.
   - Suporte nativo a **Split APKs / App Bundles** (`base.apk`, `split_config.*.apk`).
   - Validação automática de integridade ZIP e detecção de arquivos DEX.

3. **Engenharia Reversa & Descompilação (JADX):**
   - Descompilação de APKs para código fonte completo em Java/Kotlin estruturado em Gradle.
   - Suporte direto a abertura visual no **JADX-GUI** para navegação gráfica rápida.

4. **Descompilação Adobe AIR & SWF Flash (JPEXS FFDec):**
   - Extração de SWFs e manifestos embutidos em aplicativos Adobe AIR.
   - Exportação automática de scripts ActionScript 3 (`.as`), sprites/imagens (`.png`, `.jpg`) e áudios (`.mp3`, `.wav`).
   - Acesso direto ao **JPEXS FFDec GUI**.

5. **Gerenciamento e Controle de Aplicativos:**
   - Sideloading e instalação de APKs (`adb-tools install <caminho.apk>`).
   - Desinstalação limpa e remoção de dados/cache (`adb-tools clear <pacote>`).
   - Inicialização remota de apps no aparelho (`adb-tools launch <pacote>`).
   - Captura de tela instantânea em alta definição (`adb-tools screenshot`).

---

## 📁 Estrutura do Projeto

```
C:\dev\s_ADB_Tools\
├── adb_tools\
│   ├── __init__.py         # Pacote e exports do SDK
│   ├── adb_client.py       # Wrapper avançado de baixo nível ADB
│   ├── extractor.py        # Extração e validação de APKs simples e split
│   ├── decompiler.py       # Orquestração do JADX e Java 17
│   ├── air_extractor.py    # Extração de assets e SWFs de apps Adobe AIR
│   ├── ffdec_manager.py    # Gerenciador e CLI do JPEXS FFDec
│   └── cli.py              # Interface CLI e Menu Interativo Unificado
├── tools\
│   ├── jadx\               # Motor JADX v1.5.6 (jadx.bat, jadx-gui.bat)
│   └── ffdec\              # Motor JPEXS FFDec (ffdec.jar, ffdec.bat)
├── extracted_apks\          # Diretório onde os APKs extraídos são salvos
├── decompiled_sources\     # Diretório dos códigos-fonte descompilados
├── capturas\               # Diretório de screenshots salvas do aparelho
├── tests\                  # Suíte de testes automatizados com pytest
│   ├── test_extractor.py
│   ├── test_decompiler.py
│   ├── test_air_extractor.py
│   └── test_ffdec.py
├── adb-tools.bat           # LANÇADOR UNIFICADO (Menu ou argumentos CLI)
├── tools.bat               # Alias rápido para adb-tools.bat
├── main.py                 # Ponto de entrada Python
├── pytest.ini              # Configuração do pytest
├── requirements.txt        # Dependências mínimas
└── README.md
```

---

## 🚀 Como Usar

### 1. Menu Interativo Unificado
Basta dar um duplo clique em `adb-tools.bat` (ou executar no terminal):

```cmd
adb-tools
```

### 2. Comandos Diretos via Linha de Comando (CLI)

```cmd
# Listar dispositivos e bateria
adb-tools devices

# Listar aplicativos de terceiros instalados
adb-tools list

# Buscar pacotes por termo
adb-tools search whatsapp

# Extrair APK de um aplicativo
adb-tools extract com.whatsapp

# Descompilar APK para código fonte Java/Gradle
adb-tools decompile extracted_apks/com.whatsapp/base.apk

# Abrir APK na interface gráfica JADX-GUI
adb-tools gui extracted_apks/com.whatsapp/base.apk

# Capturar tela do aparelho em PNG
adb-tools screenshot

# Instalar um APK no dispositivo
adb-tools install meu-app.apk
```

---

## 🧪 Testes Automatizados

Para rodar a suíte de testes:

```cmd
pytest
```
