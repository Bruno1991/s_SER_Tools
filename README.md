# s_SER_Tools 3.0 - Suíte Universal de Engenharia Reversa e Análise de Segurança

[![GitHub](https://img.shields.io/badge/GitHub-Bruno1991%2Fs__SER__Tools-181717?style=flat-square&logo=github)](https://github.com/Bruno1991/s_SER_Tools)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-24%2B-339933?style=flat-square&logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![REA Engine](https://img.shields.io/badge/REA_Engine-morluto%2Frea-5c4ee5?style=flat-square)](https://github.com/morluto/rea)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

Suíte multiplataforma de alta performance para **Engenharia Reversa**, **Auditoria de Vulnerabilidades** e **Análise de Segurança de Software**. 

Evoluída a partir do canivete suíço Android (`s_ADB_Tools`), a **s_SER_Tools** integra em uma arquitetura modular unificada:
- **Ecossistema Android:** Gestão de aparelhos via ADB (USB e TCP/IP), extração de APKs e Split APKs/Bundles, descompilação Java/Kotlin (JADX) e engenharia reversa de Adobe AIR / Flash SWF (JPEXS FFDec).
- **Binários Nativos & Desktop:** Análise estrutural de executáveis Windows PE (`.exe`, `.dll`, `.sys`) e Linux/Android ELF (`.so`), cálculo de entropia de seções (detecção de packers) e extrator de strings/URLs/IPs.
- **Diagnóstico de Mitigações (Checksec):** Verificação automatizada de ASLR, DEP/NX, Stack Canaries (/GS), SafeSEH, Control Flow Guard (CFG), PIE, RELRO e Authenticode.
- **Aplicações Web & Electron:** Desempacotador nativo de pacotes `.asar` e auditor de configurações críticas de segurança (OWASP Electron Checklist).
- **Auditoria de Segurança & SAST:** Varredura de credenciais e chaves vazadas (AWS, GCP, OpenAI, GitHub, Stripe, URIs de banco com senha), análise do `AndroidManifest.xml` (OWASP MASVS) e geração de **relatórios executivos em HTML responsivo, Markdown e JSON**.
- **Engine REA (morluto/rea):** Orquestração direta do motor *Reverse Engineer Anything*, expondo mais de 150 comandos CLI e 200 ferramentas MCP para agentes e assistentes de Inteligência Artificial.

---

## ⚡ Principais Capacidades da Suíte

### 1. 🤖 Módulo Android
- Detecção e telemetria de aparelhos físicos e emuladores via ADB (`ser-tools devices`).
- Extração de pacotes instalados com validação de integridade ZIP e detecção de arquivos DEX (`ser-tools extract <pacote>`).
- Descompilação completa para Java estruturado em Gradle e abertura rápida no **JADX-GUI** (`ser-tools decompile`, `ser-tools gui`).
- Desempacotamento de APKs Adobe AIR e exportação de scripts ActionScript 3 (`.as`), sprites e áudios via JPEXS FFDec (`ser-tools air`, `ser-tools ffdec`).
- Captura de telas em alta resolução (`ser-tools screenshot`).

### 2. 🛡️ Auditoria de Vulnerabilidades & SAST
- **Motor de Detecção de Segredos:** Identifica chaves estáticas AWS (AKIA), tokens GitHub (PAT/ghp), chaves Firebase/Google (AIza), OpenAI/Anthropic, chaves privadas PEM (RSA/EC), JWT e strings de conexão de banco de dados com credenciais em texto claro.
- **Auditoria Android (OWASP MASVS):** Detecta `debuggable="true"`, `allowBackup="true"`, `usesCleartextTraffic="true"` (HTTP inseguro), componentes exportados desprotegidos e permissões perigosas.
- **Auditoria Electron:** Detecta `nodeIntegration: true`, `contextIsolation: false`, `enableRemoteModule: true`, `webSecurity: false` e `allowRunningInsecureContent: true`.
- **Relatórios Executivos:** Exporta relatórios completos com cálculo de nota de segurança (A+ a F), matriz de risco, evidências mascaradas e passos de remediação técnica.

### 3. 🖥️ Binários Nativos & Checksec
- **Análise PE:** Inspeção de cabeçalhos DOS/NT, tabela de seções, importações/exportações, cálculo de entropia de Shannon e detecção de seções graváveis e executáveis ($W+X$).
- **Checksec Multiplataforma:** Diagnóstico de mitigações de memória em executáveis Windows PE e bibliotecas Linux/Android ELF.
- **Extrator de Padrões:** Varredura em binários extraindo URLs, endereços IPv4 e emails.

### 4. ⚡ Integração REA Engine & MCP para IA
- Conexão nativa com a engine **REA** ([morluto/rea](https://github.com/morluto/rea)).
- Suporte a Model Context Protocol (MCP) para conectar assistentes de IA (Antigravity IDE, Claude Code, Cursor, Codex).
- Diagnóstico integrado (`ser-tools doctor`).

---

## 📁 Estrutura do Projeto

```
c:\dev\s_SER_Tools\
├── ser_tools\
│   ├── core\               # Configurações centrais, console Rich e gerador de relatórios
│   │   ├── config.py       # Detecção de caminhos, ambiente (Node, Java, ADB, REA)
│   │   ├── logger.py       # Console Rich, banners visuais e temas de severidade
│   │   └── reporter.py     # Gerador de relatórios executivos em HTML, Markdown e JSON
│   ├── android\            # Ferramentas Android
│   │   ├── adb_client.py   # Wrapper avançado de baixo nível ADB
│   │   ├── extractor.py    # Extração e validação de APKs simples e Split APKs
│   │   ├── decompiler.py   # Orquestração do JADX CLI e JADX-GUI
│   │   ├── air_extractor.py# Desempacotamento de Adobe AIR e SWF
│   │   └── ffdec_manager.py# Automação do JPEXS Free Flash Decompiler (FFDec)
│   ├── desktop_bin\        # Análise de Binários Nativos
│   │   ├── pe_analyzer.py  # Inspeção PE (.exe, .dll), entropia e seções
│   │   ├── checksec.py     # Diagnóstico de mitigações (ASLR, DEP, Canary, SafeSEH, CFG, PIE)
│   │   └── strings_extractor.py # Extrator de strings ASCII/Unicode, URLs e IPs
│   ├── web_electron\       # Aplicações Web e Electron
│   │   ├── asar_extractor.py    # Desempacotador nativo de pacotes .asar
│   │   └── electron_auditor.py  # Auditoria de regras de segurança OWASP Electron
│   ├── audit\              # Auditoria de Vulnerabilidades
│   │   ├── secrets_scanner.py   # Scanner de tokens e credenciais vazadas
│   │   ├── android_auditor.py   # Auditor de AndroidManifest.xml (OWASP MASVS)
│   │   └── suite_auditor.py     # Orquestrador universal de auditoria
│   ├── rea_engine\         # Integração com morluto/rea
│   │   ├── client.py       # Wrapper de comandos CLI do REA
│   │   ├── mcp_bridge.py   # Provedor de configuração de servidor MCP para IA
│   │   └── environment.py  # Diagnóstico da engine REA e provedores
│   └── cli\
│       ├── main_cli.py     # Despachante de comandos da linha de comando
│       └── tui.py          # Interface interativa de terminal moderna (Rich TUI)
├── adb_tools\              # Fachada de compatibilidade retroativa
├── tools\
│   ├── jadx\               # Motor JADX v1.5.6 (jadx.bat, jadx-gui.bat)
│   └── ffdec\              # Motor JPEXS FFDec v26.3.0 (ffdec.jar, ffdec.bat)
├── reports\                # Relatórios de segurança gerados (.html, .md, .json)
├── extracted_apks\          # Diretório dos APKs extraídos
├── decompiled_sources\     # Diretório dos códigos-fonte descompilados
├── capturas\               # Screenshots salvas dos dispositivos
├── tests\                  # Suíte de testes automatizados com pytest (30+ testes)
├── ser-tools.bat           # Lançador principal no Windows
├── ser.bat                 # Alias rápido do lançador
├── adb-tools.bat           # Alias legado de compatibilidade
├── main.py                 # Ponto de entrada Python
└── requirements.txt        # Dependências do projeto
```

---

## 🚀 Como Usar

### 1. Menu Interativo Moderno (TUI)
Para abrir o menu interativo com interface visual moderna no terminal:

```cmd
ser-tools
```
*(ou simplesmente execute `ser` ou duplo clique em `ser-tools.bat`)*

---

### 2. Comandos Diretos via Linha de Comando (CLI)

#### 🩺 Diagnóstico e Status da Suíte
```cmd
ser-tools doctor
```

#### 🛡️ Auditoria de Segurança e Vulnerabilidades
```cmd
# Auditar um aplicativo APK, executável PE, arquivo ASAR ou diretório de projeto
ser-tools audit extracted_apks/app.apk

# Auditar e exportar relatório especificamente em HTML e Markdown
ser-tools audit C:\caminho\projeto --format all --output reports\auditoria_alvo
```

#### 🛡️ Diagnóstico de Mitigações de Binário (Checksec)
```cmd
# Verificar proteções ASLR, DEP, Canaries, SafeSEH e CFG em um executável
ser-tools checksec app.exe

# Verificar proteções PIE, NX, Canaries e RELRO em uma biblioteca nativa .so
ser-tools checksec libnative.so
```

#### 🖥️ Análise Estrutural PE e Strings
```cmd
# Inspecionar cabeçalhos, seções, importações de DLLs e assinatura digital
ser-tools pe app.exe

# Extrair URLs, IPs e emails de um binário
ser-tools strings app.exe
```

#### 🌐 Desempacotamento Electron ASAR
```cmd
ser-tools asar app.asar --output C:\caminho\extraido
```

#### 🤖 Gestão e Engenharia Reversa Android
```cmd
# Listar dispositivos conectados e nível de bateria
ser-tools devices

# Listar aplicativos instalados
ser-tools list

# Buscar pacotes
ser-tools search whatsapp

# Extrair APK do aparelho
ser-tools extract com.whatsapp

# Descompilar APK para código Java/Gradle
ser-tools decompile extracted_apks/com.whatsapp/base.apk

# Abrir APK na interface gráfica JADX-GUI
ser-tools gui extracted_apks/com.whatsapp/base.apk

# Capturar tela do aparelho
ser-tools screenshot
```

#### ⚡ Comandos da Engine REA (morluto/rea)
```cmd
# Listar provedores e motores configurados no REA
ser-tools rea providers

# Analisar aplicação JavaScript/Electron com REA
ser-tools rea analyze-javascript-application C:\caminho\app
```

---

## 🧪 Testes Automatizados

A suíte possui cobertura de testes automatizados com `pytest`:

```cmd
pytest -v
```

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte `LICENSE` para mais informações.
