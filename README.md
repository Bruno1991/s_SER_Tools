# s_ADB_Tools - Gerenciador, Extrator & Descompilador de APKs

Ferramenta completa desenvolvida em Python para localizar, extrair do smartphone Android via ADB e descompilar APKs em código-fonte Java, Kotlin, XML e recursos Web (Cordova/HTML5).

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

---

## Estrutura do Projeto

```
C:\dev\s_ADB_Tools\
├── adb_tools\
│   ├── __init__.py
│   ├── adb_client.py       # Wrapper de conexão ADB
│   ├── extractor.py        # Extração e validação de APKs
│   ├── decompiler.py       # Orquestração do JADX, Java 17 e extração de fontes
│   └── cli.py              # Interface CLI e menu interativo
├── tools\
│   └── jadx\               # Binários do JADX (jadx.bat, jadx-gui.bat)
├── extracted_apks\          # Onde os APKs extraídos do celular são salvos
│   └── com.smartexpenditure\
│       └── com.smartexpenditure.apk
├── decompiled_sources\     # Onde os códigos-fonte descompilados ficam salvos
│   └── com.smartexpenditure\
│       ├── app\
│       │   ├── src\main\
│       │   │   ├── AndroidManifest.xml
│       │   │   ├── java\
│       │   │   ├── res\
│       │   │   └── assets\www\ (HTML, JS, CSS do app)
│       ├── build.gradle
│       └── settings.gradle
├── tests\
│   ├── test_extractor.py
│   └── test_decompiler.py
├── extrair-apk.bat         # Menu interativo do extrator
├── descompilar-apk.bat     # Atalho para descompilar APK
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
- **`abrir-jadx-gui.bat`**: Abre a interface gráfica do JADX para navegar no código com busca de texto e grafo de chamadas.

### 2. Pelo Terminal (CLI)

- **Extrair APK do celular:**
  ```powershell
  python main.py extract com.smartexpenditure
  # ou usando parte do nome:
  python main.py extract gastos
  ```

- **Descompilar o APK extraído:**
  ```powershell
  python main.py decompile com.smartexpenditure
  ```

- **Abrir o APK no JADX-GUI:**
  ```powershell
  python main.py gui com.smartexpenditure
  ```

- **Listar aplicativos instalados:**
  ```powershell
  python main.py list
  ```

---

## Aplicativo Analisado: `com.smartexpenditure` ("Gastos")

- **Tipo de Aplicativo:** Aplicativo Híbrido Android + Apache Cordova.
- **Fontes Java gerados:** 9.656 arquivos `.java` em `app/src/main/java`.
- **Recursos XML:** 360 arquivos em `app/src/main/res`.
- **Código Web Original:** 100% dos scripts JavaScript (`main.js`, `buttons.actions.js`, `pt.js`), páginas HTML e estilos CSS preservados intactos em:
  `C:\dev\s_ADB_Tools\decompiled_sources\com.smartexpenditure\app\src\main\assets\www\`
