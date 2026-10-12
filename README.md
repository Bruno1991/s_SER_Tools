# s_ADB_Tools - Gerenciador, Extrator & Descompilador de APKs

Ferramenta completa desenvolvida em Python para localizar, extrair do smartphone Android via ADB e descompilar APKs em código-fonte Java, Kotlin, XML, recursos Web (Cordova/HTML5) e jogos/aplicativos **Adobe AIR / Flash (ActionScript 3 / SWF)**.

---

## Principais Recursos

1. **Conexão e Extração ADB:**
   - Detecta automaticamente o `adb.exe` em `C:\dev\platform-tools`, no PATH ou no Android SDK.
   - Lista dispositivos conectados e verifica autorização de Depuração USB.
   - Busca pacotes por nome ou palavra-chave e extrai APKs completos (com suporte a *split APKs*).
   - Valida integridade do arquivo ZIP e verifica arquivos `.dex`.

2. **Engenharia Reversa e Descompilação (JADX Integrado):**
   - Integração nativa com **JADX v1.5.6** e suporte a **Java 17 OpenJDK** (`C:\dev\jdk-17.0.2`).
   - Download e instalação automática do motor descompilador caso não esteja presente.
   - Gera projeto completo estruturado em Gradle (`app/src/main/java`, `res`, `AndroidManifest.xml`).
   - Suporte a descompilação de aplicativos híbridos (recupera 100% dos arquivos JavaScript, CSS, HTML e plugins Cordova em `assets/www`).
   - Atalho integrado para abrir o **JADX-GUI** para inspeção visua3. **Módulo Especializado Adobe AIR / Flash (SWF & ActionScript 3):**
   - Detecta automaticamente aplicativos criados com Adobe AIR (ex: Slither.io, jogos Flash portados).
   - Analisa o descritor nativo `application.xml` (ID, versão, renderMode, fullscreen, ANEs).
   - Extrai o SWF principal do jogo e todos os SWFs de extensões nativas (ANEs).
   - Extrai todos os recursos de áudio (MP3, OGG), texturas e dados de jogo.
   - Gera relatório técnico detalhado `AIR_ANALYSIS.md`.

4. **Motor Descompilador SWF Integrado (JPEXS Free Flash Decompiler - FFDec):**
   - Download e configuração automática do **JPEXS FFDec v26.3.0** em `tools/ffdec`.
   - Exportação em massa via CLI de classes ActionScript 3 (`.as`), spritesheets/imagens (`.png`, `.jpg`), sons (`.wav`, `.mp3`) e dados binários.
   - Atalho integrado para abrir o **FFDec GUI** para visualização visual de sprites, vetores e scripts.
   - Gera mapeamento completo da arquitetura de IA, física e protocolo (`SLITHER_CODE_ARCHITECTURE.md`).

---

## Estrutura do Projeto

```
C:\dev\s_ADB_Tools\
├── adb_tools\
│   ├── __init__.py
│   ├── adb_client.py       # Wrapper de conexão ADB
│   ├── extractor.py        # Extração e validação de APKs
│   ├── decompiler.py       # Orquestração do JADX, Java 17 e detecção AIR
│   ├── air_extractor.py    # Extração de SWF, ANEs e análise de Adobe AIR
│   ├── ffdec_manager.py    # Gerenciador, CLI e GUI do JPEXS FFDec
│   └── cli.py              # Interface CLI e menu interativo
├── tools\
│   ├── jadx\               # Binários do JADX (jadx.bat, jadx-gui.bat)
│   └── ffdec\              # Binários do FFDec (ffdec.jar, ffdec.bat, ffdec.exe)
├── extracted_apks\          # Onde os APKs extraídos do celular são salvos
│   ├── com.smartexpenditure.apk
│   └── air.com.hypah.io.slither.apk
├── decompiled_sources\     # Onde os códigos-fonte descompilados ficam salvos
│   ├── com.smartexpenditure\
│   │   └── app\src\main\assets\www\
│   └── air.com.hypah.io.slither\
│       ├── app\src\main\java\ (Stubs C++/Java do AIR Runtime)
│       ├── air_extracted\     (SWFs brutos, application.xml, game_assets)
│       ├── actionscript_src\  (195 classes .as, 48 imagens/skins, 6 áudios)
│       └── SLITHER_CODE_ARCHITECTURE.md (Mapeamento de IA, física e rede)
├── tests\
│   ├── test_extractor.py
│   ├── test_decompiler.py
│   ├── test_air_extractor.py
│   └── test_ffdec.py
├── extrair-apk.bat         # Menu interativo principal
├── descompilar-apk.bat     # Atalho para descompilar APK (Java/XML)
├── extrair-air-swf.bat     # Atalho para extrair SWF/Assets de apps Adobe AIR
├── descompilar-swf.bat     # Atalho para descompilar SWF em ActionScript 3 e assets (FFDec)
├── abrir-jadx-gui.bat      # Atalho para abrir interface gráfica do JADX
├── abrir-ffdec-gui.bat     # Atalho para abrir interface gráfica do FFDec
├── listar-apps.bat         # Atalho para listar apps do aparelho
├── main.py                 # Ponto de entrada CLI
├── requirements.txt
└── README.md
```

---

## Como Usar

### 1. Atalhos com Duplo-Clique (Windows)
- **`extrair-apk.bat`**: Abre o menu principal interativo com todas as funções (1 a 10).
- **`descompilar-apk.bat`**: Pergunta qual APK/pacote descompilar e gera o código Java/XML via JADX.
- **`descompilar-swf.bat`**: Descompila o SWF em código ActionScript 3 e assets imediatamente via FFDec.
- **`extrair-air-swf.bat`**: Extrai o SWF principal e extensões de jogos Adobe AIR.
- **`abrir-jadx-gui.bat`**: Abre a interface gráfica do JADX para navegar no código Java.
- **`abrir-ffdec-gui.bat`**: Abre a interface gráfica do FFDec para navegar no SWF do Flash.

### 2. Pelo Terminal (CLI)

- **Descompilar SWF em ActionScript 3 & Assets (FFDec):**
  ```powershell
  python main.py ffdec air.com.hypah.io.slither
  ```

- **Abrir o SWF no JPEXS FFDec GUI:**
  ```powershell
  python main.py ffdec-gui air.com.hypah.io.slither
  ```

- **Extrair APK do celular:**
  ```powershell
  python main.py extract air.com.hypah.io.slither
  ```

- **Extrair e Analisar Aplicativo Adobe AIR:**
  ```powershell
  python main.py air air.com.hypah.io.slither
  ```

- **Descompilar APK em Java / XML (JADX):**
  ```powershell
  python main.py decompile air.com.hypah.io.slither
  ```

---

## Aplicativos Analisados

### 1. `com.smartexpenditure` ("Gastos")
- **Tipo de Aplicativo:** Aplicativo Híbrido Android + Apache Cordova.
- **Fontes Java gerados:** 9.656 arquivos `.java` em `app/src/main/java`.
- **Recursos XML:** 360 arquivos em `app/src/main/res`.
- **Código Web Original:** 100% dos scripts JavaScript (`main.js`, `buttons.actions.js`, `pt.js`), páginas HTML e estilos CSS preservados intactos em `decompiled_sources/com.smartexpenditure/app/src/main/assets/www/`.

### 2. `air.com.hypah.io.slither` ("Slither.io")
- **Tipo de Aplicativo:** Jogo Adobe AIR (Flash / ActionScript 3 sobre Starling Stage3D).
- **Classes ActionScript 3 recuperadas:** 195 arquivos `.as` em `actionscript_src/scripts` (incluindo `gaim.Main`, `gaim.Snake`, `hypah.mode4.Mode4Socket`).
- **Assets de Jogo exportados:** 48 imagens e mipmaps de skins (`sheet0_a_png` a `sheet3_g_png`), 6 efeitos sonoros (turbo/boost, menus) e fundos de arena.
- **Engenharia Reversa Completa:** Documentação técnica em [SLITHER_CODE_ARCHITECTURE.md](file:///c:/dev/s_ADB_Tools/decompiled_sources/air.com.hypah.io.slither/SLITHER_CODE_ARCHITECTURE.md) detalhando:
  - IA dos bots offline (comportamento de *Avoidance Steering*, modo predatório *Violent Mode* e alimentação *Foraging*).
  - Protocolo binário de rede Slither v5+ (handshake CRC32, opcodes `'a'`, `'g'`, `'e'`, `'d'`, `'s'` e controle de 1 byte de direção e boost).
  - Física de movimento proporcional ao tamanho da cobra e perda de massa por turbo.
- **Visualizador Gráfico:** Utilize o script `abrir-ffdec-gui.bat` para abrir e navegar interativamente no SWF e em todas as sprites.
