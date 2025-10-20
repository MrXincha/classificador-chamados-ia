# Assistente ITSM com IA 🤖✨

Um projeto acadêmico de um assistente virtual (chatbot) para Service Desk de TI, construído com Python, Flask e a API Google Gemini. O sistema visa simular um portal de autoatendimento onde usuários podem reportar problemas, solicitar serviços e receber soluções proativas baseadas em uma Base de Conhecimento, tudo através de uma interface de chat inteligente.

## 📜 Descrição

Este projeto implementa um hub de serviços de TI que centraliza a interação do usuário através de um chatbot. A IA (Google Gemini) é utilizada para:

1.  **Compreender** a solicitação ou problema do usuário em linguagem natural.
2.  **Consultar** uma Base de Conhecimento (KB) para oferecer soluções passo a passo para problemas comuns (Nível 1).
3.  **Classificar** automaticamente novos chamados (Incidentes ou Requisições) em categorias ITSM pré-definidas.
4.  **Estimar** a prioridade do chamado com base na descrição.
5.  **Pedir esclarecimentos** caso a solicitação do usuário seja ambígua.

O sistema web, construído com Flask, gerencia a autenticação de usuários, o armazenamento de chamados, comentários, anexos e categorias em um banco de dados SQLite, e apresenta uma interface de dashboard moderna inspirada em sistemas como o Gemini.

## ✅ Funcionalidades Principais

* **Autenticação de Usuários:** Cadastro e Login seguros.
* **Hub Central:** Dashboard com saudação personalizada e resumo dos chamados do usuário (Abertos, Resolvidos, Ocultos).
* **Interface de Chatbot:** Interação principal para abrir chamados e receber suporte.
* **Base de Conhecimento (KB):** Soluções proativas com passos detalhados para problemas comuns (Internet, Impressora, Senha, Office, etc.).
* **Criação Inteligente de Chamados:**
    * Classificação automática (Categoria ITSM).
    * Definição automática (Incidente vs. Requisição).
    * Estimativa de Prioridade (Baixa, Média, Alta, Urgente).
    * Atribuição simulada de Responsável (baseado na categoria).
* **Gerenciamento de Chamados (Usuário):**
    * Visualização de detalhes do chamado (status, prioridade, responsável, histórico).
    * Adição de comentários.
    * Upload de anexos (limite de 16MB, tipos definidos).
    * Opção de Ocultar/Reexibir chamados.
* **Página "Meus Chamados":** Lista completa do histórico de chamados do usuário.
* **Gerenciamento de Categorias:** Interface para adicionar/remover categorias ITSM (populada inicialmente com categorias padrão).

## 🚀 Tecnologias Utilizadas

* **Backend:** Python 3, Flask
* **Banco de Dados:** SQLite (via Flask-SQLAlchemy)
* **Autenticação:** Flask-Login
* **Inteligência Artificial:** Google Gemini API (via `google-generativeai`)
* **Frontend:** HTML5, CSS3 (Bootstrap 5, Ícones Bootstrap), JavaScript (Vanilla JS)
* **Variáveis de Ambiente:** `python-dotenv`
* **Utilitários:** Werkzeug (para uploads seguros)

## 🔧 Como Executar Localmente

Siga estes passos para configurar e rodar o projeto na sua máquina:

**Pré-requisitos:**

* Python 3.8 ou superior instalado.
* Git instalado.
* Uma chave de API do Google Gemini (obtenha em [Google AI Studio](https://aistudio.google.com/)).

**Instalação:**

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/](https://github.com/)[SEU-USUARIO-GITHUB]/[NOME-DO-REPOSITORIO].git
    cd [NOME-DO-REPOSITORIO]
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Linux / macOS
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    *(Certifique-se de ter um arquivo `requirements.txt` no seu repositório)*
    ```bash
    pip install -r requirements.txt
    ```
    *Se você ainda não tem o `requirements.txt`, gere-o no seu ambiente com:*
    ```bash
    pip freeze > requirements.txt
    # (Não se esqueça de adicionar este arquivo ao Git!)
    ```

4.  **Configure as Variáveis de Ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione sua chave da API do Gemini a este arquivo:
        ```env
        GOOGLE_API_KEY=SUA_CHAVE_API_AQUI
        # Você também pode adicionar uma SECRET_KEY para o Flask (opcional, mas recomendado)
        # SECRET_KEY=uma_chave_secreta_muito_forte_e_aleatoria
        ```

5.  **Crie a Pasta de Uploads:**
    * Na raiz do projeto, crie uma pasta chamada `uploads`.

6.  **Execute a Aplicação:**
    ```bash
    flask run
    ```

7.  Acesse `http://127.0.0.1:5000` (ou o endereço fornecido) no seu navegador.

## 🎮 Uso Básico

1.  **Registre-se:** Crie uma nova conta fornecendo nome, sobrenome, e-mail e senha. Os outros campos são opcionais.
2.  **Faça Login:** Use seu e-mail e senha.
3.  **Interaja com o Chatbot:** Descreva seu problema ou solicitação na caixa de chat na página inicial.
    * Se for um problema comum, o bot oferecerá uma solução passo a passo.
    * Se for complexo, ambíguo ou você recusar a solução, um chamado será criado.
4.  **Gerencie seus Chamados:** Use as abas no Hub ou o menu "Meus Chamados" para ver seu histórico. Clique em um chamado para ver detalhes, adicionar comentários ou anexos.
5.  **Gerencie Categorias:** Use o menu "Categorias" para adicionar ou remover categorias personalizadas (as básicas são criadas automaticamente).
