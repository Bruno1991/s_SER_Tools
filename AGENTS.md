# Diretriz Global de Autonomia Total e Pré-Autorização do Agente

## 1. Autorização Prévia e Autonomia Total (100% Autônomo)
O operador humano (`Bruno1991`) concedeu **autorização prévia irrestrita e permanente** para o agente executar qualquer tarefa técnica no workspace `C:\dev` e em todos os seus subprojetos e diretórios.

O agente **NÃO DEVE** interromper o fluxo nem solicitar confirmações manuais para:
- **Arquivos:** Ler, criar, modificar, renomear ou remover arquivos de código, configurações, documentações e testes dentro de `C:\dev`;
- **Ambiente & Pacotes:** Criar ambientes virtuais (`.venv`), instalar pacotes e dependências (`pip`, `npm`, `cargo`, etc.);
- **Execução & Testes:** Rodar scripts, comandos de terminal, servidores de desenvolvimento, linters, checagens de tipos e suítes de testes automatizados (`pytest`, `npm test`, etc.);
- **Correções em Loop:** Aplicar correções de erros, refatorações e autofix até que todas as validações passem com 100% de sucesso;
- **Versionamento & Git:** Criar branches, adicionar alterações (`git add`), gerar commits estruturados (Conventional Commits) e fazer `git push` para os repositórios remotos do usuário configurados em `C:\dev\.env`;
- **Decisões Técnicas:** Definir arquiteturas, padrões de projeto, modelagem de dados, algoritmos e bibliotecas adequadas.

## 2. Princípio de Execução Não Interativa
- Assuma total responsabilidade técnica de ponta a ponta pelo resultado final.
- Prossiga de forma autônoma e contínua até o objetivo estar completamente cumprido.
- Em caso de dúvidas técnicas secundárias, adote a alternativa mais robusta, segura e reversível com base na `engineering-library` e execute sem bloquear o trabalho.

## 3. Salvaguardas de Segurança do Agente
- **Segurança de Segredos:** Nunca grave tokens reais, senhas ou credenciais em código ou commits; utilize sempre referências às variáveis do arquivo `C:\dev\.env`.
- **Garantia de Qualidade:** Execute a validação e testes automatizados antes de concluir qualquer entrega ou realizar push.
- **Isolamento de Escopo:** Todas as alterações devem permanecer estritamente contidas no diretório `C:\dev`.
