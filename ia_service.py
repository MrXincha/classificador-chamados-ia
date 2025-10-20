import os
import google.generativeai as genai
import json

# --- BASE DE CONHECIMENTO ENRIQUECIDA ---
# Agora com passos detalhados em HTML
KNOWLEDGE_BASE = [
    {
        "keywords": ["nao liga", "não liga", "computador morto", "pc nao liga", "desktop nao liga", "notebook nao liga", "sem energia", "morreu", "não acende"],
        "solution_html": """
<p>Um computador que não liga pode ser assustador, mas geralmente é algo simples na parte de energia. Vamos checar:</p>
<ol>
    <li><strong>Verifique os Cabos de Energia:</strong> O cabo está firme na tomada e na fonte do computador (aquela caixa atrás do gabinete)? Se for um notebook, o carregador está bem conectado nele e na tomada? Tente desconectar e reconectar ambos os lados.</li>
    <li><strong>Teste a Tomada:</strong> A tomada está funcionando? Tente ligar outro aparelho (como um carregador de celular ou um abajur) nela para confirmar.</li>
    <li><strong>Verifique o Filtro de Linha/Estabilizador (Régua):</strong> Se você usa uma, veja se o botão de 'ligar' dela está aceso. Tente ligar o computador direto na tomada da parede, bypassando a régua/estabilizador.</li>
    <li><strong>Verifique a Fonte (para Desktops):</strong> Muitos gabinetes têm um pequeno interruptor (geralmente I/O) na parte de trás, perto de onde o cabo de energia entra. Veja se ele está na posição 'I' (ligado).</li>
    <li><strong>Teste Rápido do Notebook (Reset de Energia):</strong> Se for um notebook, desconecte o carregador, segure o botão de ligar por 15 segundos (para descarregar a energia residual) e depois tente ligá-lo novamente (primeiro só na bateria, depois com o carregador).</li>
</ol>
        """,
        "follow_up": "Algum desses passos fez o equipamento dar algum sinal de vida (acender luzes, fazer barulho) ou ele continua totalmente 'morto'?"
    },
    {
        "keywords": ["internet", "wifi", "lenta", "sem conexão", "caiu", "rede", "navegar", "não conecta", "sem internet"],
        "solution_html": """
<p>Problemas de conexão são comuns. Siga estes passos para tentar resolver:</p>
<ol>
    <li><strong>Reinicie Modem e Roteador:</strong> Desligue ambos da tomada, espere 30 segundos e ligue-os novamente (primeiro o modem que recebe o sinal da rua, espere todas as luzes estabilizarem, depois ligue o roteador Wi-Fi).</li>
    <li><strong>Verifique as Luzes dos Equipamentos:</strong> No modem, as luzes 'Power', 'DS/US' ou 'Internet/WAN' devem estar acesas e estáveis (não piscando rapidamente ou vermelhas). No roteador, 'Power', 'Internet/WAN' e 'Wi-Fi' devem estar normais.</li>
    <li><strong>Cheque os Cabos:</strong> Confirme que o cabo de rede entre o modem e o roteador está firme nas duas pontas. Se você usa cabo direto no computador, verifique essa conexão também.</li>
    <li><strong>Teste em Outro Dispositivo:</strong> Seu celular conecta no Wi-Fi? Outro computador na rede funciona? Isso ajuda a saber se o problema é só no seu equipamento ou na rede toda.</li>
    <li><strong>Esqueça a Rede Wi-Fi e Reconecte:</strong> No seu computador ou celular, vá nas configurações de Wi-Fi, mande "Esquecer" a rede e conecte-se novamente, digitando a senha.</li>
    <li><strong>Reinicie seu Computador/Celular:</strong> Muitas vezes, só isso já resolve.</li>
</ol>
        """,
        "follow_up": "Após seguir esses passos, sua conexão voltou ao normal ou o problema persiste?"
    },
    {
        "keywords": ["impressora", "imprimir", "não imprime", "erro impressão", "fila presa", "offline"],
        "solution_html": """
<p>Impressora dando dor de cabeça? Vamos tentar o básico antes de chamar o suporte:</p>
<ol>
    <li><strong>Verifique o Óbvio na Impressora:</strong> Ela está ligada? Tem papel na bandeja correta? Tem tinta/toner suficiente? Há alguma mensagem de erro ou luz piscando no painel dela?</li>
    <li><strong>Reinicie Tudo (Ciclo de Energia):</strong> Desligue a impressora E o seu computador. Ligue a impressora primeiro, espere ela inicializar completamente, e só então ligue o computador.</li>
    <li><strong>Limpe a Fila de Impressão (Windows):</strong>
        <ul>
            <li>Digite "Impressoras e scanners" na busca do Windows e abra.</li>
            <li>Clique na sua impressora e depois em "Abrir fila".</li>
            <li>No menu "Impressora", clique em "Cancelar todos os documentos". Confirme se pedir.</li>
            <li>Se algum documento não sumir, reinicie o computador e verifique a fila novamente.</li>
        </ul>
    </li>
    <li><strong>Verifique a Conexão:</strong> Se for USB, o cabo está firme no PC e na impressora? Tente outra porta USB. Se for de rede (Wi-Fi ou cabo), a impressora está conectada na mesma rede que o seu computador?</li>
</ol>
        """,
        "follow_up": "Algum desses passos fez a impressora voltar a funcionar ou o problema continua?"
    },
     {
        "keywords": ["senha", "esqueci", "bloqueada", "resetar", "acesso", "expirou", "trocar senha"],
        "solution_html": """
<p>Problemas com senha ou acesso bloqueado? Temos algumas opções:</p>
<ol>
    <li><strong>Opção 'Esqueci minha senha':</strong> A maioria dos sistemas (Windows, e-mail, sistemas internos) tem um link na tela de login para redefinir a senha. Tente usá-lo primeiro.</li>
    <li><strong>Central de Autoatendimento:</strong> Se sua empresa possui uma ferramenta específica para gestão de senhas, utilize-a. Acesse: <a href='https://sistema.de.reset.com' target='_blank'>[Link da Ferramenta Interna]</a></li>
    <li><strong>Verifique Caps Lock:</strong> Parece bobo, mas confira se a tecla Caps Lock (Fixa) não está ativada por acidente.</li>
</ol>
        """,
        "follow_up": "Conseguiu recuperar seu acesso com esses passos ou ainda está bloqueado?"
    },
    {
        "keywords": ["excel lento", "word travando", "outlook nao abre", "outlook lento", "office lento", "programa travou", "excel travou", "powerpoint lento"],
        "solution_html": """
<p>Programas do Office (Word, Excel, Outlook) estão lentos ou travando? Tente o seguinte:</p>
<ol>
    <li><strong>Reinicie o Programa e o Computador:</strong> Feche o aplicativo completamente (use Ctrl+Shift+Esc para o Gerenciador de Tarefas se precisar forçar) e reabra. Se persistir, reinicie o computador.</li>
    <li><strong>Verifique Atualizações:</strong> Abra qualquer programa do Office, vá em 'Arquivo' > 'Conta' > 'Opções de Atualização' > 'Atualizar Agora'. Mantenha o Office atualizado.</li>
    <li><strong>Tente o 'Modo de Segurança' do Office:</strong>
        <ul>
            <li>Feche o programa (ex: Excel).</li>
            <li>Pressione e segure a tecla <strong>Ctrl</strong>.</li>
            <li>Clique no ícone do programa para abri-lo, mantendo o Ctrl pressionado até uma caixa de confirmação aparecer.</li>
            <li>Clique em 'Sim' para iniciar em Modo de Segurança.</li>
        </ul>
        Se funcionar bem em Modo de Segurança, o problema provavelmente é um Suplemento. Vá em 'Arquivo > Opções > Suplementos', selecione 'Suplementos COM' em 'Gerenciar' e clique 'Ir...'. Desmarque os suplementos suspeitos e reinicie o programa normalmente.
    </li>
    <li><strong>Reparo Rápido do Office (Windows):</strong> Digite "Adicionar ou remover programas" na busca, encontre seu pacote Microsoft Office, clique em 'Modificar' e escolha a opção 'Reparo Rápido'.</li>
</ol>
        """,
        "follow_up": "O programa voltou ao normal após esses passos, ou o problema continua?"
    },
    {
        "keywords": ["sem som", "audio nao funciona", "mudo", "caixa de som", "fone de ouvido", "nao sai som", "microfone", "não me ouvem"],
        "solution_html": """
<p>Problemas com som ou microfone? Vamos verificar as configurações:</p>
<ol>
    <li><strong>Cheque o Volume e o Mudo:</strong> Clique no ícone de alto-falante perto do relógio. O volume está baixo ou no mudo (ícone com 'x')? Se for problema no microfone, verifique se ele não está no mudo no próprio fone ou no aplicativo (Teams, Zoom, etc).</li>
    <li><strong>Selecione o Dispositivo Correto:</strong> No mesmo menu de volume, clique na setinha (^) ou no nome do dispositivo atual. Garanta que a 'Saída' (para ouvir) e a 'Entrada' (para falar) estejam selecionadas para o dispositivo que você quer usar (ex: Fone de ouvido, Alto-falantes Realtek).</li>
    <li><strong>Verifique as Conexões Físicas:</strong> O cabo do fone/caixa de som está bem conectado (geralmente na porta verde para som, rosa para microfone)? Se for USB, tente outra porta. O microfone externo está ligado?</li>
    <li><strong>Teste em Outro Aplicativo:</strong> O som/microfone funciona no YouTube, mas não no Teams? Ou vice-versa? Isso indica um problema de configuração no aplicativo específico. Verifique as configurações de áudio dentro do aplicativo que está falhando.</li>
    <li><strong>Reinicie o Computador:</strong> A clássica reinicialização pode recarregar os drivers de áudio/microfone.</li>
</ol>
        """,
        "follow_up": "O áudio ou microfone voltou a funcionar corretamente ou o problema persiste?"
    },
    {
        "keywords": ["vpn", "nao conecta vpn", "sem acesso vpn", "conexao vpn", "cisco", "forticlient", "globalprotect"],
        "solution_html": """
<p>Problemas para conectar na VPN da empresa? Tente estes passos:</p>
<ol>
    <li><strong>Verifique sua Internet Base:</strong> Sua conexão Wi-Fi ou cabeada está funcionando normalmente? Tente acessar um site público (como google.com) antes de tentar a VPN. A VPN precisa de uma internet estável para funcionar.</li>
    <li><strong>Verifique as Credenciais:</strong> Você está digitando o usuário e senha (ou token/código 2FA) corretos? Senhas expiram, tokens atualizam.</li>
    <li><strong>Reinicie o Aplicativo VPN:</strong> Feche completamente o cliente VPN (Cisco AnyConnect, FortiClient, GlobalProtect, etc.) e abra-o novamente.</li>
    <li><strong>Verifique Atualizações do Cliente VPN:</strong> O aplicativo está atualizado? Às vezes, versões antigas são bloqueadas por segurança. Verifique se há atualizações dentro do próprio aplicativo.</li>
    <li><strong>Reinicie o Computador:</strong> Isso reinicia os serviços de rede que a VPN utiliza.</li>
</ol>
        """,
        "follow_up": "Conseguiu conectar na VPN ou continua com problemas de acesso?"
    },
    {
        "keywords": ["monitor", "sem video", "tela preta", "segundo monitor", "nao detecta monitor", "resolucao", "tela piscando"],
        "solution_html": """
<p>Problemas com o monitor ou segunda tela? Vamos checar as conexões e configurações:</p>
<ol>
    <li><strong>Verifique os Cabos:</strong> O cabo de vídeo (HDMI, DisplayPort, VGA) está BEM conectado TANTO no monitor QUANTO no computador/notebook/docking station? Desconecte e reconecte firmemente as duas pontas.</li>
    <li><strong>Verifique a Energia do Monitor:</strong> O monitor está ligado na tomada e o botão de energia dele está aceso (geralmente uma luz azul ou branca)?</li>
    <li><strong>Selecione a Entrada Correta no Monitor:</strong> Use os botões físicos no próprio monitor para navegar no menu dele e garantir que a 'Fonte de Entrada' (Input Source) está selecionada corretamente (HDMI 1, HDMI 2, DisplayPort, etc.), correspondendo ao cabo que você está usando.</li>
    <li><strong>Para Segundo Monitor (Windows):</strong> Pressione as teclas 'Windows + P' juntas. Um menu aparecerá na lateral. Certifique-se de que 'Estender' ou 'Duplicar' está selecionado (e não 'Somente tela do PC' ou 'Somente segunda tela').</li>
    <li><strong>Reinicie o Computador:</strong> Especialmente se o problema começou após uma atualização ou hibernação.</li>
</ol>
        """,
        "follow_up": "A imagem apareceu no monitor ou o problema persiste?"
    },
    {
        "keywords": ["computador lento", "pc lento", "notebook lento", "demorando", "travando muito"],
        "solution_html": """
<p>Computador lento pode ter várias causas, mas podemos tentar algumas otimizações básicas:</p>
<ol>
    <li><strong>Reinicie o Computador:</strong> Se você não reinicia há muitos dias, faça isso agora. É a solução mais eficaz para liberar memória e processos presos.</li>
    <li><strong>Feche Programas Desnecessários:</strong> Quantos programas estão abertos ao mesmo tempo? Feche navegadores com muitas abas, aplicativos que você não está usando ativamente. Use o Gerenciador de Tarefas (Ctrl+Shift+Esc) para ver o que está consumindo mais CPU ou Memória e finalize tarefas se souber o que está fazendo.</li>
    <li><strong>Verifique Espaço em Disco:</strong> Seu disco principal (geralmente C:) está quase cheio? Clique com o botão direito nele no 'Explorador de Arquivos', vá em 'Propriedades'. Se tiver menos de 10-15% de espaço livre, isso causa lentidão. Use a ferramenta 'Limpeza de Disco' do Windows para liberar espaço.</li>
    <li><strong>Verifique Atualizações do Windows:</strong> Vá em 'Configurações > Atualização e Segurança > Windows Update' e clique em 'Verificar se há atualizações'. Instale todas as atualizações pendentes e reinicie.</li>
    <li><strong>Execute uma Verificação de Vírus:</strong> Use o antivírus instalado para fazer uma verificação completa do sistema.</li>
</ol>
        """,
        "follow_up": "O computador melhorou o desempenho após esses passos ou continua muito lento?"
    },
    {
        "keywords": ["mouse", "teclado", "nao funciona", "sem fio", "parou", "nao digita", "cursor travado"],
        "solution_html": """
<p>Mouse ou teclado parou de funcionar? Vamos checar o básico:</p>
<ol>
    <li><strong>Se for Sem Fio (Wireless):</strong>
        <ul>
            <li>Verifique as pilhas ou a bateria. Tente trocar as pilhas ou carregar o dispositivo.</li>
            <li>Existe um botão físico de Ligar/Desligar (On/Off) embaixo do mouse/teclado? Verifique se está ligado.</li>
            <li>O receptor USB (dongle) está bem conectado ao computador? Tente trocar de porta USB.</li>
        </ul>
    </li>
    <li><strong>Se for Com Fio (USB):</strong>
        <ul>
            <li>O cabo USB está bem conectado ao computador? Tente trocar de porta USB.</li>
            <li>Verifique se há alguma luz acesa no dispositivo (Num Lock, Caps Lock no teclado; luz óptica embaixo do mouse).</li>
        </ul>
    </li>
    <li><strong>Reinicie o Computador:</strong> Isso força o Windows a redetectar os dispositivos USB.</li>
    <li><strong>Teste em Outro Computador (se possível):</strong> Conecte o mouse/teclado em outro PC para ver se ele funciona lá. Isso ajuda a saber se o problema é no dispositivo ou no seu computador.</li>
</ol>
        """,
        "follow_up": "O mouse ou teclado voltou a funcionar depois dessas verificações?"
    }
]


def get_chatbot_response(user_message: str, categories: list, force_ticket: bool = False) -> dict:
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"response": "Erro: API Key não configurada.", "action": "none"}

        genai.configure(api_key=api_key)

        kb_string = json.dumps(KNOWLEDGE_BASE)  # Converte a KB para string

        # --- NOVO PROMPT MESTRE v4.2 ---
        prompt = f"""
        Você é um agente de Service Desk de TI Nível 1 (L1). Seu objetivo é resolver problemas comuns com a Base de Conhecimento (KB) ou criar um chamado estruturado se necessário.
        A mensagem original do usuário é: "{user_message}"

        **Flag de Forçar Chamado:** {force_ticket}
        **Base de Conhecimento (KB) com Soluções Detalhadas:** {kb_string}
        **Categorias ITSM Válidas:** {', '.join(categories)}

        **Instruções de Processamento (SIGA ESTRITAMENTE):**

        1.  **Analise a mensagem original:** "{user_message}".
        2.  **Avalie a Complexidade:**
            * **Problemas Complexos (Exigem Ticket Direto):** Se a mensagem indicar falha grave de hardware (ex: "PC soltando fumaça", "tela quebrada"), erro crítico de sistema (ex: "tela azul", "não inicializa"), alerta de segurança (ex: "vírus", "phishing"), ou for uma solicitação clara de serviço (ex: "instalar software", "criar conta"), **pule para o Passo 5 (Criar Chamado)**.
            * **Problemas Simples (Tentar Resolver com KB):** Se for um problema comum de conectividade, acesso, impressão, ou uso básico de software, **continue para o Passo 3**.
            * **Em caso de dúvida**, considere o problema como simples e tente a KB.

        3.  **Verifique a Flag 'Forçar Chamado'.**
            * **SE 'True'**: Ignore a KB e **vá direto para o Passo 5 (Criar Chamado)** usando a mensagem original.

        4.  **Verifique a KB (SE 'Forçar Chamado' for 'False' E o problema for 'Simples'):**
            * **SE a mensagem corresponder** a uma 'keyword' da KB:
                * Responda com um JSON 'propose_solution' neste formato exato:
                    {{
                        "action": "propose_solution",
                        "solution_html": "O texto HTML detalhado de 'solution_html' da KB",
                        "follow_up": "O texto de 'follow_up' da KB"
                    }}
            * **SE NÃO corresponder à KB (mesmo sendo simples):**
                * **Vá para o Passo 5 (Criar Chamado)**.

        5.  **Crie um Chamado (SE Complexo OU Forçado OU Simples sem KB):**
            * Baseado na mensagem original ("{user_message}"), gere um JSON 'create_ticket' neste formato exato:
                {{
                    "action": "create_ticket",
                    "title": "Um título curto e claro para o problema '{user_message}'",
                    "ticket_type": "Incidente ou Requisição",
                    "priority": "Baixa, Média, Alta ou Urgente (estime pela descrição e complexidade)",
                    "category": "A Categoria ITSM Válida MAIS APROPRIADA para '{user_message}'",
                    "response": "A mensagem de confirmação para o usuário (ex: 'Entendido. Como este parece ser um problema mais complexo, abri o chamado #... para você sobre ... A equipe responsável entrará em contato.')"
                }}

        Gere APENAS o objeto JSON da sua decisão final (propose_solution ou create_ticket). NÃO inclua nenhuma outra explicação.
        """

        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)

        # Tenta interpretar a resposta da IA
        try:
            # Remove possíveis blocos de código markdown que a IA às vezes adiciona
            cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()
            action_data = json.loads(cleaned_response)

            # Validação básica do JSON retornado
            if 'action' not in action_data or action_data['action'] not in ['propose_solution', 'create_ticket']:
                raise ValueError("JSON da IA não contém 'action' válida.")

            return action_data

        except (json.JSONDecodeError, TypeError, ValueError, Exception) as e:
            print(f"Erro ao processar resposta da IA: {e}\nResposta Bruta: {response.text}")
            # Fallback: Se a IA falhar ou retornar algo inesperado, cria um chamado genérico
            fallback_category = categories[0] if categories else "Geral"
            return {
                "action": "create_ticket",
                "title": f"Problema reportado: {user_message[:50]}...",  # Título genérico
                "ticket_type": "Incidente",
                "priority": "Média",
                "category": fallback_category,
                "response": f"Entendi. Abri um chamado genérico (#{'{ticket_id}'}) para investigar seu problema: '{user_message[:50]}...'. A equipe entrará em contato."
                # Placeholder para ID
            }

    except Exception as e:
        print(f"Ocorreu um erro GERAL na função get_chatbot_response: {e}")
        return {"response": "Desculpe, estou com um problema interno grave. Tente novamente mais tarde.",
                "action": "error"}