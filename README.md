# Sistema de Base de Conhecimento TIC

Sistema web multi-usuário para gerenciamento de base de conhecimento do setor de gerenciamento e suporte de TIC.

## Características Principais

- **Autenticação de Usuários**: Sistema completo de login com diferentes níveis de permissão
- **Editor HTML Robusto**: Criação de Procedimentos Operacionais Padrão (POPs) com suporte a imagens
- **Gestão de Arquivos**: Upload e referência de arquivos PDF e ZIP
- **Categorização**: Sistema de categorias e tags para organização do conteúdo
- **Controle de Status**: Fluxo de trabalho com status (rascunho, em análise, homologado, arquivado)
- **Busca Avançada**: Busca por título, categoria, tags ou conteúdo
- **Design Intuitivo**: Interface limpa com ícones para melhor ambientação do usuário

## Requisitos Técnicos

- Python 3.8+
- Flask
- MySQL
- Bibliotecas Python (ver requirements.txt)

## Instalação

1. Clone o repositório
2. Configure o ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Configure o banco de dados MySQL:
   - Crie um banco de dados chamado `mydb`
   - Configure as credenciais no arquivo `src/main.py` ou use variáveis de ambiente

5. Inicialize o banco de dados:
   ```
   python src/main.py
   ```

## Execução

Para iniciar o servidor de desenvolvimento:

```
python src/main.py
```

O sistema estará disponível em `http://localhost:5000`

## Usuário Padrão

Ao inicializar o sistema, um usuário administrador é criado automaticamente:

- **Usuário**: admin
- **Senha**: admin123

**Importante**: Altere a senha do administrador após o primeiro login.

## Estrutura do Projeto

```
knowledge_base_app/
├── venv/                  # Ambiente virtual Python
├── src/                   # Código-fonte da aplicação
│   ├── models/            # Modelos de dados
│   ├── routes/            # Rotas e controladores
│   ├── static/            # Arquivos estáticos (CSS, JS)
│   ├── templates/         # Templates HTML
│   └── main.py            # Ponto de entrada da aplicação
├── uploads/               # Diretório para arquivos enviados
└── requirements.txt       # Dependências do projeto
```

## Funcionalidades Detalhadas

### Gerenciamento de Artigos
- Criação, edição e visualização de artigos
- Editor HTML completo com suporte a imagens
- Categorização e adição de tags
- Controle de status (rascunho, em análise, homologado, arquivado)
- Histórico de alterações

### Gestão de Arquivos
- Upload de arquivos PDF, ZIP e imagens
- Associação de arquivos a artigos
- Referência a arquivos dentro dos artigos
- Download de arquivos

### Controle de Acesso
- Diferentes níveis de permissão (administrador, editor, usuário)
- Usuários normais só visualizam artigos homologados
- Artigos arquivados só aparecem quando solicitados na busca

### Administração
- Gerenciamento de usuários
- Criação e edição de categorias
- Monitoramento de atividades
- Dashboard com estatísticas

## Segurança

- Senhas armazenadas com hash seguro
- Proteção contra CSRF
- Validação de entradas
- Controle de acesso baseado em funções

## Suporte

Para suporte ou dúvidas, entre em contato com o administrador do sistema.
