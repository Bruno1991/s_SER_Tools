# s_ADB_Tools - Gerenciador e Extrator de APKs via ADB

Ferramenta desenvolvida em Python para localizar, inspecionar e extrair pacotes APK diretamente de smartphones Android conectados via depuração USB (ADB).

---

## Recursos

- **Detecção Automática:** Localiza o executável `adb.exe` em `C:\dev\platform-tools`, no PATH do sistema ou no Android SDK.
- **Busca Rápida de Aplicativos:** Filtra pacotes instalados por palavra-chave ou nome parcial.
- **Extração com Validação:** Baixa os arquivos APK e valida a integridade do arquivo ZIP/DEX baixado.
- **Suporte a Split APKs:** Trata tanto APKs únicos (`base.apk`) quanto pacotes divididos por arquitetura/densidade (`split_config.*.apk`).
- **Zero Dependências Externas:** Funciona imediatamente com Python 3 padrão (sem necessidade de instalar pacotes via pip).
- **Menu Interativo e CLI:** Pode ser executado com menu interativo pelo terminal ou via argumentos de linha de comando.

---

## Estrutura do Projeto

```
C:\dev\s_ADB_Tools\
├── adb_tools\
│   ├── __init__.py
│   ├── adb_client.py    # Wrapper de baixo nível para comandos ADB
│   ├── extractor.py     # Lógica de download e validação de integridade
│   └── cli.py           # Menus interativos e parser de argumentos
├── extracted_apks\      # Diretório onde os APKs extraídos são salvos
│   └── com.smartexpenditure.apk
├── tests\
│   └── test_extractor.py
├── extrair-apk.bat      # Atalho com duplo clique no Windows
├── listar-apps.bat      # Atalho para listar apps de terceiros
├── main.py              # Ponto de entrada CLI
├── requirements.txt
└── README.md
```

---

## Como Usar

### 1. Modo Interativo (Mais Fácil)
Dê um duplo clique em `extrair-apk.bat` ou execute:
```powershell
python main.py
```
Um menu interativo será exibido com as opções:
1. Listar dispositivos conectados
2. Buscar e extrair APK
3. Listar todos os apps instalados
4. Abrir pasta de APKs extraídos

### 2. Linha de Comando (CLI Direto)

- **Listar dispositivos conectados:**
  ```powershell
  python main.py devices
  ```

- **Buscar um pacote:**
  ```powershell
  python main.py search gastos
  python main.py search expend
  ```

- **Listar todos os aplicativos de terceiros:**
  ```powershell
  python main.py list
  ```

- **Extrair o APK de um aplicativo específico:**
  ```powershell
  python main.py extract com.smartexpenditure
  # ou usando parte do nome:
  python main.py extract gastos
  ```

---

## Aplicativo Extraído nesta Sessão

- **Nome do App:** Gastos / Smart Expenditure
- **Pacote:** `com.smartexpenditure`
- **Arquivo local:** [com.smartexpenditure.apk](file:///c:/dev/s_ADB_Tools/extracted_apks/com.smartexpenditure.apk) (8.62 MB)
- **Estrutura interna:** Contém `classes.dex`, `classes2.dex` e recursos originais em XML compilado. Sem código nativo C/C++, tornando a descompilação com ferramentas como **JADX** 100% direta.
