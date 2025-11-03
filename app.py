import os
import random
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db, User, Ticket, Category, TicketComment, KnowledgeBaseItem, Attachment
from ia_service import get_chatbot_response
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

load_dotenv()

app: Flask = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-bem-dificil-de-adivinhar')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB por upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'zip'}
db.init_app(app)
migrate = Migrate(app, db)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    if Category.query.first() is None:
        print("Detectado banco de dados de categorias vazio. Populando com dados básicos...")

        basic_categories = [
            "Incidente - Hardware",
            "Incidente - Software / Aplicações",
            "Incidente - Rede e Conectividade",
            "Incidente - Contas e Acessos",
            "Incidente - Periféricos",
            "Incidente - Facilities / Manutenção Predial",
            "Requisição - Hardware",
            "Requisição - Software / Aplicações",
            "Requisição - Contas e Acessos"
        ]

        # Adiciona cada categoria ao banco de dados
        for cat_name in basic_categories:
            new_category = Category(name=cat_name)
            db.session.add(new_category)

        # Salva todas as novas categorias no banco
        db.session.commit()
        print("Categorias básicas populadas com sucesso!")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Verifique seu email e senha.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_date_str = request.form.get('birth_date')
        employee_code = request.form.get('employee_code') or None

        if User.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'warning')
            return redirect(url_for('register'))

        birth_date_obj = None
        if birth_date_str:
            try:
                birth_date_obj = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
                return redirect(url_for('register'))

        agent_code = os.environ.get('AGENT_REGISTRATION_CODE')

        is_new_agent = False
        if agent_code and employee_code == agent_code:
            is_new_agent = True

        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date_obj,
            employee_code=employee_code,
            is_agent=is_new_agent
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        if is_new_agent:
            flash('Conta de AGENTE criada com sucesso! Faça o login.', 'success')
        else:
            flash('Conta criada com sucesso! Faça o login.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html')  #


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- NOVA ROTA DE PERFIL ---
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Verifica qual formulário foi enviado
        form_type = request.form.get('form_type')

        if form_type == 'update_details':
            # Lógica para atualizar nome e sobrenome
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            db.session.commit()
            flash('Seus dados foram atualizados com sucesso!', 'success')
            return redirect(url_for('profile'))

        elif form_type == 'update_password':
            # Lógica para atualizar a senha
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_user.check_password(old_password):
                flash('A senha antiga está incorreta.', 'danger')
                return redirect(url_for('profile'))

            if new_password != confirm_password:
                flash('As novas senhas não coincidem.', 'danger')
                return redirect(url_for('profile'))

            if len(new_password) < 6:  # Adicionando uma verificação simples de tamanho
                flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
                return redirect(url_for('profile'))

            current_user.set_password(new_password)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('profile'))

    return render_template('profile.html', active_page='profile')


# --- FIM DA NOVA ROTA ---


@app.route('/')
@login_required
def index():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "Bom dia"
    elif 12 <= hour < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"

    # Chamados Abertos e Visíveis
    open_tickets = Ticket.query.filter(
        Ticket.requester == current_user,
        Ticket.status.in_(['Aberto', 'Em Andamento', 'Pendente']),
        Ticket.is_hidden == False
    ).order_by(Ticket.updated_at.desc()).all()

    # Chamados Resolvidos
    resolved_tickets = Ticket.query.filter(
        Ticket.requester == current_user,
        Ticket.status.in_(['Resolvido', 'Fechado']),
        Ticket.is_hidden == False
    ).order_by(Ticket.resolved_at.desc()).limit(10).all()  # Mostra só os 10 últimos

    # Chamados Ocultos
    hidden_tickets = Ticket.query.filter(
        Ticket.requester == current_user,
        Ticket.is_hidden == True
    ).order_by(Ticket.updated_at.desc()).all()

    return render_template('index.html',
                           greeting=greeting,
                           open_tickets=open_tickets,
                           resolved_tickets=resolved_tickets,
                           hidden_tickets=hidden_tickets,
                           active_page='hub')


@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message')
    force_ticket = data.get('force_ticket', False)

    if not user_message:
        return jsonify({'response': 'Mensagem vazia recebida.'}), 400

    if len(user_message) > 5000:
        return jsonify({'response': 'Sua mensagem é muito longa (máx 5000 caracteres). Por favor, resuma o problema.'})

    categories_obj = Category.query.all()
    category_names = [cat.name for cat in categories_obj]
    if not category_names: category_names = ["Geral"]

    ai_result = get_chatbot_response(user_message, category_names, force_ticket)

    if ai_result.get('action') == 'create_ticket':
        try:
            category_obj = Category.query.filter_by(name=ai_result.get('category')).first()
            if not category_obj: category_obj = Category.query.first()

            new_ticket = Ticket(
                title=ai_result.get('title'),
                ticket_type=ai_result.get('ticket_type'),
                priority=ai_result.get('priority'),
                status='Aberto',
                requester=current_user,
                category_obj=category_obj,
                responsible_user_id=None
            )
            db.session.add(new_ticket)
            db.session.flush()

            initial_comment = TicketComment(
                description=user_message,
                ticket_id=new_ticket.id,
                author=current_user,
                is_internal=False  # O primeiro comentário do usuário nunca é interno
            )
            db.session.add(initial_comment)
            db.session.commit()

            final_response = ai_result.get('response').replace('#...', f'#{new_ticket.id}')

            return jsonify({
                'response': final_response,
                'action': 'ticket_created',
                'ticket_id': new_ticket.id,
                'ticket_title': new_ticket.title,
                'ticket_status': new_ticket.status,
                'ticket_description': user_message,
                'ticket_url': url_for('ticket_detail', ticket_id=new_ticket.id)
            })

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar ticket: {e}")
            return jsonify({'response': 'Tive um problema ao criar seu chamado. A equipe de TI foi notificada.'})

    return jsonify(ai_result)


def get_ticket_or_404(ticket_id):
    """Helper para garantir que o ticket exista e pertença ao usuário."""
    return Ticket.query.filter_by(id=ticket_id, user_id=current_user.id).first_or_404()


@app.route('/ticket/hide/<int:ticket_id>', methods=['POST'])
@login_required
def hide_ticket(ticket_id):
    ticket = get_ticket_or_404(ticket_id)
    ticket.is_hidden = True
    db.session.commit()
    flash('Chamado ocultado com sucesso.', 'info')
    return redirect(url_for('index'))


@app.route('/ticket/unhide/<int:ticket_id>', methods=['POST'])
@login_required
def unhide_ticket(ticket_id):
    ticket = get_ticket_or_404(ticket_id)
    ticket.is_hidden = False
    db.session.commit()
    flash('Chamado reexibido com sucesso.', 'success')
    return redirect(url_for('index'))


@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    # Protegendo a rota - Somente agentes
    if not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        category_name = request.form.get('category_name')
        if category_name:
            existing_category = Category.query.filter_by(name=category_name).first()
            if not existing_category:
                new_category = Category(name=category_name)
                db.session.add(new_category)
                db.session.commit()
                flash('Categoria adicionada com sucesso!', 'success')
            else:
                flash('Essa categoria já existe.', 'warning')
        return redirect(url_for('manage_categories'))

    all_categories = Category.query.order_by(Category.name).all()
    return render_template('categories.html', categories=all_categories,
                           active_page='categories')


@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    # Protegendo a rota - Somente agentes
    if not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    category_to_delete = Category.query.get_or_404(category_id)
    db.session.delete(category_to_delete)
    db.session.commit()
    flash('Categoria removida com sucesso!', 'success')
    return redirect(url_for('manage_categories'))


def get_responsible_for_category(category_name):
    teams = {
        "Hardware": ["João Silva (Equipe Hardware)", "Marcos (N1)"],
        "Software / Aplicações": ["Equipe de Aplicações", "Ana Pereira (Sistemas)"],
        "Rede e Conectividade": ["Equipe de Redes (Roteadores)", "Carlos (Telecom)"],
        "Contas e Acessos": ["Segurança da Informação", "Admin Service Desk"],
        "Periféricos": ["Equipe de Hardware", "Suporte Local"],
        "Facilities / Manutenção Predial": ["Equipe de Manutenção", "Ricardo (Zeladoria)"]
    }
    for key, team in teams.items():
        if key in category_name:
            return random.choice(team)
    return "Triagem (Service Desk)"


@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # 1. VERIFICAÇÃO DE "VER" (VIEW)
    # Permite ver se for o dono OU qualquer agente.
    if ticket.user_id != current_user.id and not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    # 2. VERIFICAÇÃO: QUEM PODE POSTAR?
    can_post_comment = False
    if current_user.id == ticket.user_id:
        can_post_comment = True  # O dono (requisitante) sempre pode postar
    elif current_user.is_agent and current_user.id == ticket.responsible_user_id:
        can_post_comment = True  # O agente responsável pode postar

    # 3. LÓGICA DE "POSTAR" (POST)
    if request.method == 'POST':

        # 4. VERIFICAÇÃO DE PERMISSÃO NO POST
        if not can_post_comment:
            flash('Você não pode adicionar comentários a um chamado que não é seu.', 'danger')
            return redirect(url_for('ticket_detail', ticket_id=ticket.id))

        new_comment_text = request.form.get('comment_text')
        file = request.files.get('attachment_file')

        # --- MUDANÇA (Feature 2) ---
        # Verifica se o checkbox "Nota Interna" foi marcado
        is_internal_note = request.form.get('is_internal') == 'on'
        # --- FIM DA MUDANÇA ---

        if new_comment_text:
            if len(new_comment_text) > 5000:
                flash('Comentário muito longo (máx 5000 caracteres).', 'danger')
                return redirect(url_for('ticket_detail', ticket_id=ticket.id))

            new_comment = TicketComment(
                description=new_comment_text,
                ticket_id=ticket.id,
                author=current_user,
                is_internal=is_internal_note  # <-- MUDANÇA (Feature 2)
            )
            db.session.add(new_comment)

        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            storage_name = f"{os.urandom(12).hex()}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], storage_name))

            new_attachment = Attachment(
                ticket_id=ticket.id,
                user_id=current_user.id,
                storage_filename=storage_name,
                original_filename=filename
            )
            db.session.add(new_attachment)

        if new_comment_text or (file and file.filename != ''):
            ticket.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            flash('Chamado atualizado com sucesso!', 'success')

        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    # 5. LÓGICA DE "VER" (GET)
    comments = TicketComment.query.filter_by(ticket_id=ticket.id).order_by(TicketComment.created_at.asc()).all()
    attachments = Attachment.query.filter_by(ticket_id=ticket.id).order_by(Attachment.uploaded_at.desc()).all()

    # 6. PASSANDO A NOVA VARIÁVEL
    return render_template('ticket_detail.html',
                           ticket=ticket,
                           comments=comments,
                           attachments=attachments,
                           can_post=can_post_comment)


@app.route('/download_attachment/<string:filename>')
@login_required
def download_attachment(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route('/my_tickets')
@login_required
def my_tickets():
    all_tickets = Ticket.query.filter(
        Ticket.requester == current_user,
        Ticket.is_hidden == False
    ).order_by(Ticket.updated_at.desc()).all()

    return render_template('my_tickets.html', tickets=all_tickets, active_page='my_tickets')


@app.route('/agent/queue')
@login_required
def agent_queue():
    if not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    unassigned_tickets = Ticket.query.filter(
        Ticket.responsible_user_id == None,
        Ticket.status.notin_(['Resolvido', 'Fechado'])
    ).order_by(Ticket.created_at.asc()).all()

    assigned_to_me = Ticket.query.filter(
        Ticket.responsible_user_id == current_user.id,
        Ticket.status.notin_(['Resolvido', 'Fechado'])
    ).order_by(Ticket.created_at.asc()).all()

    return render_template('agent_queue.html',
                           unassigned_tickets=unassigned_tickets,
                           assigned_to_me=assigned_to_me,
                           active_page='queue')


@app.route('/agent/ticket/assign/<int:ticket_id>', methods=['POST'])
@login_required
def agent_assign_ticket(ticket_id):
    # 1. Proteger a rota: Somente agentes podem fazer isso
    if not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    # 2. Encontrar o chamado
    ticket = Ticket.query.get_or_404(ticket_id)

    # 3. Verificar se o chamado já não foi pego por outro agente
    if ticket.responsible_user_id is not None:
        flash(f'O chamado #{ticket.id} já foi assumido por outro agente.', 'warning')
        return redirect(url_for('agent_queue'))

    # 4. Assumir o chamado!
    ticket.responsible_user_id = current_user.id
    ticket.status = 'Em Andamento'  # Opcional: Mudar status ao assumir
    ticket.updated_at = datetime.now(timezone.utc)  # Atualiza o timestamp

    db.session.commit()

    flash(f'Você assumiu o chamado #{ticket.id}!', 'success')

    # 5. Redirecionar o agente para a página do chamado que ele acabou de pegar
    return redirect(url_for('ticket_detail', ticket_id=ticket.id))


@app.route('/agent/ticket/status/<int:ticket_id>', methods=['POST'])
@login_required
def agent_update_status(ticket_id):
    # 1. Proteger a rota: Somente agentes podem fazer isso
    if not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    # 2. Encontrar o chamado
    ticket = Ticket.query.get_or_404(ticket_id)

    # 3. VERIFICAÇÃO DE POSSE (A NOVA LÓGICA)
    # Um agente só pode mudar o status de um chamado QUE ESTÁ ATRIBUÍDO A ELE.
    if ticket.responsible_user_id != current_user.id:
        flash(f'Você não pode modificar o chamado #{ticket.id} pois ele não está atribuído a você.', 'danger')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    # 4. Pegar o novo status do formulário
    new_status = request.form.get('new_status')

    # 5. Validar o status
    valid_statuses = ['Aberto', 'Em Andamento', 'Pendente', 'Resolvido', 'Fechado']
    if new_status not in valid_statuses:
        flash(f'Status "{new_status}" inválido.', 'danger')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    # 6. Atualizar o chamado
    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)  # Atualiza o timestamp

    # 7. Lógica de Resolução:
    # Se o status for Resolvido/Fechado, preenche a data de resolução
    if new_status in ['Resolvido', 'Fechado']:
        if ticket.resolved_at is None:
            ticket.resolved_at = datetime.now(timezone.utc)
    else:
        # Se for reaberto (ex: de 'Pendente' para 'Em Andamento'), limpa a data
        ticket.resolved_at = None

    db.session.commit()
    flash(f'Status do chamado #{ticket.id} atualizado para "{new_status}".', 'success')

    # 8. Voltar para a página do chamado
    return redirect(url_for('ticket_detail', ticket_id=ticket.id))


# --- NOVA ROTA (Feature 1) ---
@app.route('/agent/ticket/unassign/<int:ticket_id>', methods=['POST'])
@login_required
def agent_unassign_ticket(ticket_id):
    # 1. Proteger a rota: Somente agentes podem fazer isso
    if not current_user.is_agent:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    # 2. Encontrar o chamado
    ticket = Ticket.query.get_or_404(ticket_id)

    # 3. VERIFICAÇÃO DE POSSE
    # Só o agente responsável pode devolver o chamado
    if ticket.responsible_user_id != current_user.id:
        flash(f'Você não pode devolver um chamado que não é seu.', 'danger')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    # 4. Devolver o chamado!
    ticket.responsible_user_id = None
    ticket.status = 'Aberto'  # Devolve para o status inicial
    ticket.updated_at = datetime.now(timezone.utc)

    db.session.commit()

    flash(f'Chamado #{ticket.id} devolvido à fila.', 'success')

    # 5. Redirecionar o agente de volta para a fila
    return redirect(url_for('agent_queue'))


# --- FIM DA NOVA ROTA ---


@app.route('/user/ticket/review/<int:ticket_id>', methods=['POST'])
@login_required
def user_review_ticket(ticket_id):
    # 1. Pegar o status do formulário ("Fechado" ou "Em Andamento")
    new_status = request.form.get('new_status')

    # 2. Validação simples
    if new_status not in ['Em Andamento', 'Fechado']:
        flash('Ação inválida.', 'danger')
        # request.referrer é um truque para mandar o usuário de volta
        # para a página exata de onde ele veio.
        return redirect(request.referrer or url_for('index'))

    # 3. Pegar o chamado
    ticket = Ticket.query.get_or_404(ticket_id)

    # 4. A VERIFICAÇÃO DE SEGURANÇA MAIS IMPORTANTE:
    # O usuário logado é o DONO do chamado?
    if ticket.user_id != current_user.id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    # 5. VERIFICAÇÃO DE LÓGICA:
    # O usuário só pode reabrir/fechar um chamado que está "Resolvido"
    if ticket.status != 'Resolvido':
        flash('Este chamado não está pendente de revisão.', 'warning')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    # Se todas as verificações passarem, atualizamos o chamado:
    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)

    if new_status == 'Em Andamento':
        # Significa que o usuário REABRIU o chamado
        ticket.resolved_at = None  # Limpamos a data de resolução
        db.session.commit()
        flash(f'Chamado #{ticket.id} foi reaberto com sucesso.', 'success')
    else:
        # Significa que o usuário FECHOU o chamado
        # A data 'resolved_at' já estava preenchida, então só salvamos
        db.session.commit()
        flash(f'Chamado #{ticket.id} fechado com sucesso. Obrigado!', 'success')

    return redirect(url_for('ticket_detail', ticket_id=ticket.id))


if __name__ == '__main__':
    app.run(debug=True)

