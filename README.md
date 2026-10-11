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
   - Atalho integrado para abrir o **JADX-GUI** para inspeção visual rápida de código.

3. **Módulo Especializado Adobe AIR / Flash (SWF & ActionScript 3):**
   - Detecta automaticamente aplicativos criados com Adobe AIR (ex: Slither.io, jogos Flash portados).
   - Analisa o descritor nativo `application.xml` (ID, versão, renderMode, fullscreen, ANEs).
   - Extrai o SWF principal do jogo e todos os SWFs de extensões nativas (ANEs).
   - Extrai todos os recursos de áudio (MP3, OGG), texturas e dados de jogo.
   - Gera relatório técnico detalhado `AIR_ANALYSIS.md` e guia passo a passo para descompilar o código ActionScript 3 usando o **JPEXS Free Flash Decompiler (FFDec)**.

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
│   └── cli.py              # Interface CLI e menu interativo
├── tools\
│   └── jadx\               # Binários do JADX (jadx.bat, jadx-gui.bat)
├── extracted_apks\          # Onde os APKs extraídos do celular são salvos
│   ├── com.smartexpenditure.apk
│   └── air.com.hypah.io.slither.apk
├── decompiled_sources\     # Onde os códigos-fonte descompilados ficam salvos
│   ├── com.smartexpenditure\
│   │   └── app\src\main\assets\www\
│   └── air.com.hypah.io.slither\
│       ├── app\src\main\java\ (Stubs C++/Java do AIR Runtime)
│       └── air_extracted\
│           ├── slither android.swf (Código ActionScript 3 e sprites do jogo)
│           ├── application.xml     (Descritor AIR)
│           ├── extension_swfs\     (Bibliotecas ANE)
│           ├── game_assets\        (Áudios, texturas, shaders)
│           └── AIR_ANALYSIS.md     (Relatório técnico e guia FFDec)
├── tests\
│   ├── test_extractor.py
│   ├── test_decompiler.py
│   └── test_air_extractor.py
├── extrair-apk.bat         # Menu interativo principal
├── descompilar-apk.bat     # Atalho para descompilar APK (Java/XML)
├── extrair-air-swf.bat     # Atalho para extrair SWF/Assets de apps Adobe AIR
├── abrir-jadx-gui.bat      # Atalho para abrir interface gráfica do JADX
├── listar-apps.bat         # Atalho para listar apps do aparelho
├── main.py                 # Ponto de entrada CLI
├── requirements.txt
└── README.md
```

---

## Como Usar

### 1. Atalhos com Duplo-Clique (Windows)
- **`extrair-apk.bat`**: Abre o menu principal interativo com todas as funções.
- **`descompilar-apk.bat`**: Pergunta qual APK/pacote descompilar e gera o código-fonte imediatamente.
- **`extrair-air-swf.bat`**: Extrai o SWF principal, extensões e gera o guia FFDec para jogos Adobe AIR.
- **`abrir-jadx-gui.bat`**: Abre a interface gráfica do JADX para navegar no código Java.

### 2. Pelo Terminal (CLI)

- **Extrair APK do celular:**
  ```powershell
  python main.py extract air.com.hypah.io.slither
  # ou usando parte do nome:
  python main.py extract slither
  ```

- **Extrair e Analisar Aplicativo Adobe AIR (SWF / ActionScript 3):**
  ```powershell
  python main.py air air.com.hypah.io.slither
  ```

- **Descompilar o APK extraído (Java / XML + auto detecção de AIR):**
  ```powershell
  python main.py decompile air.com.hypah.io.slither
  ```

- **Abrir o APK no JADX-GUI:**
  ```powershell
  python main.py gui air.com.hypah.io.slither
  ```

- **Listar aplicativos instalados:**
  ```powershell
  python main.py list
  ```

---

## Aplicativos Analisados

### 1. `com.smartexpenditure` ("Gastos")
- **Tipo de Aplicativo:** Aplicativo Híbrido Android + Apache Cordova.
- **Fontes Java gerados:** 9.656 arquivos `.java` em `app/src/main/java`.
- **Recursos XML:** 360 arquivos em `app/src/main/res`.
- **Código Web Original:** 100% dos scripts JavaScript (`main.js`, `buttons.actions.js`, `pt.js`), páginas HTML e estilos CSS preservados intactos em:
  `decompiled_sources/com.smartexpenditure/app/src/main/assets/www/`

### 2. `air.com.hypah.io.slither` ("Slither.io")
- **Tipo de Aplicativo:** Jogo Adobe AIR (Flash / ActionScript 3).
- **SWF Principal:** `slither android.swf` (27.91 MB compactado, 28.75 MB em memória, assinatura CWS).
- **Extensões Nativas (ANEs):** 9 extensões integradas (`androidx.core`, `com.jetbrains.kotlin`, `com.distriqt.*`).
- **Arquivos SWF Totais:** 55 arquivos SWF extraídos.
- **Recursos de Jogo:** 118 arquivos de áudio MP3 (músicas, efeitos sonoros de bloop/comida) e configurações.
- **Como Inspecionar o Código do Jogo:** Abra o `slither android.swf` extraído no **JPEXS Free Flash Decompiler (FFDec)** conforme detalhado em `air_extracted/AIR_ANALYSIS.md`.
