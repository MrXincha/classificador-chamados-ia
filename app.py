import os
import random
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limite de 16MB por upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'zip'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    # 1. Garante que todas as tabelas sejam criadas
    db.create_all()

    # 2. "Seeding": Popula as categorias básicas se o banco estiver vazio
    if Category.query.first() is None:
        print("Detectado banco de dados de categorias vazio. Populando com dados básicos...")

        # Lista das categorias essenciais de ITSM
        basic_categories = [
            "Incidente - Hardware",
            "Incidente - Software / Aplicações",
            "Incidente - Rede e Conectividade",
            "Incidente - Contas e Acessos",
            "Incidente - Periféricos",
            "Incidente - Facilities / Manutenção Predial",
            "Requisição - Hardware",
            "Requisição - Software / Aplicações",
            "Requisição - Contas e Acessos"  # Adicionei esta que faltava
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

        # Converte a data de string para objeto Date
        birth_date_obj = None
        if birth_date_str:
            try:
                birth_date_obj = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
                return redirect(url_for('register'))

        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date_obj,
            employee_code=employee_code
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Conta criada com sucesso! Faça o login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    # 1. Lógica da Saudação
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "Bom dia"
    elif 12 <= hour < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"

    # 2. Lógica dos Chamados
    # Buscamos o primeiro comentário (descrição) junto com o chamado.
    # Esta é uma query mais avançada, mas muito eficiente.

    # Chamados Abertos e Visíveis
    open_tickets = db.session.query(Ticket, TicketComment.description) \
        .join(TicketComment, Ticket.id == TicketComment.ticket_id) \
        .filter(
        Ticket.requester == current_user,
        Ticket.status.in_(['Aberto', 'Em Andamento', 'Pendente']),
        Ticket.is_hidden == False
    ) \
        .order_by(Ticket.updated_at.desc()) \
        .all()

    # Chamados Resolvidos
    resolved_tickets = db.session.query(Ticket, TicketComment.description) \
        .join(TicketComment, Ticket.id == TicketComment.ticket_id) \
        .filter(
        Ticket.requester == current_user,
        Ticket.status.in_(['Resolvido', 'Fechado']),
        Ticket.is_hidden == False
    ) \
        .order_by(Ticket.resolved_at.desc()) \
        .limit(10).all()  # Mostra só os 10 últimos

    # Chamados Ocultos
    hidden_tickets = db.session.query(Ticket, TicketComment.description) \
        .join(TicketComment, Ticket.id == TicketComment.ticket_id) \
        .filter(
        Ticket.requester == current_user,
        Ticket.is_hidden == True
    ) \
        .order_by(Ticket.updated_at.desc()) \
        .all()

    return render_template('index.html',
                           greeting=greeting,
                           open_tickets=open_tickets,
                           resolved_tickets=resolved_tickets,
                           hidden_tickets=hidden_tickets)


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

            responsible = get_responsible_for_category(category_obj.name)

            new_ticket = Ticket(
                title=ai_result.get('title'),
                ticket_type=ai_result.get('ticket_type'),
                priority=ai_result.get('priority'),
                status='Aberto',
                requester=current_user,
                category_obj=category_obj,
                responsible_name=responsible
            )
            db.session.add(new_ticket)
            db.session.flush()

            initial_comment = TicketComment(
                description=user_message,
                ticket_id=new_ticket.id,
                author=current_user
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
            # --- ESTE É O BLOCO CORRIGIDO ---
            db.session.rollback()  # Desfaz qualquer mudança no banco se der erro
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

# --- ROTAS DE GERENCIAMENTO DE CATEGORIAS ---

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
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
    return render_template('categories.html', categories=all_categories)

@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category_to_delete = Category.query.get_or_404(category_id)
    # No futuro, podemos adicionar uma lógica para verificar se a categoria está em uso.
    db.session.delete(category_to_delete)
    db.session.commit()
    flash('Categoria removida com sucesso!', 'success')
    return redirect(url_for('manage_categories'))

def get_responsible_for_category(category_name):
    # Dicionário "didático" de equipes e responsáveis
    teams = {
        "Hardware": ["João Silva (Equipe Hardware)", "Marcos (N1)"],
        "Software / Aplicações": ["Equipe de Aplicações", "Ana Pereira (Sistemas)"],
        "Rede e Conectividade": ["Equipe de Redes (Roteadores)", "Carlos (Telecom)"],
        "Contas e Acessos": ["Segurança da Informação", "Admin Service Desk"],
        "Periféricos": ["Equipe de Hardware", "Suporte Local"],
        "Facilities / Manutenção Predial": ["Equipe de Manutenção", "Ricardo (Zeladoria)"]
    }
    # Pega um responsável aleatório da equipe ou um padrão
    for key, team in teams.items():
        if key in category_name:
            return random.choice(team)
    return "Triagem (Service Desk)"


@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id, user_id=current_user.id).first_or_404()

    # Lógica para adicionar novo comentário e anexo
    if request.method == 'POST':
        new_comment_text = request.form.get('comment_text')
        file = request.files.get('attachment_file')

        # 1. Adiciona o comentário se ele existir
        if new_comment_text:
            if len(new_comment_text) > 5000:
                flash('Comentário muito longo (máx 5000 caracteres).', 'danger')
                return redirect(url_for('ticket_detail', ticket_id=ticket.id))

            new_comment = TicketComment(
                description=new_comment_text,
                ticket_id=ticket.id,
                author=current_user
            )
            db.session.add(new_comment)

        # 2. Adiciona o anexo se ele existir e for válido
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Cria um nome de arquivo único para salvar (evita sobreposição)
            storage_name = f"{os.urandom(12).hex()}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], storage_name))

            new_attachment = Attachment(
                ticket_id=ticket.id,
                user_id=current_user.id,
                storage_filename=storage_name,
                original_filename=filename
            )
            db.session.add(new_attachment)

        # 3. Se algo foi adicionado, salva no banco
        if new_comment_text or (file and file.filename != ''):
            ticket.updated_at = datetime.now(timezone.utc)  # Força atualização do timestamp
            db.session.commit()
            flash('Chamado atualizado com sucesso!', 'success')

        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    # Pega todos os comentários e anexos para exibir
    comments = TicketComment.query.filter_by(ticket_id=ticket.id).order_by(TicketComment.created_at.asc()).all()
    attachments = Attachment.query.filter_by(ticket_id=ticket.id).order_by(Attachment.uploaded_at.desc()).all()

    return render_template('ticket_detail.html',
                           ticket=ticket,
                           comments=comments,
                           attachments=attachments)


# Rota para baixar anexos
@app.route('/download_attachment/<string:filename>')
@login_required
def download_attachment(filename):
    # Verificação de segurança (simplificada):
    # Idealmente, verificar se o current_user tem acesso ao ticket deste anexo.
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route('/my_tickets')
@login_required
def my_tickets():
    all_tickets = db.session.query(Ticket, TicketComment.description)\
        .join(TicketComment, Ticket.id == TicketComment.ticket_id)\
        .filter(
            Ticket.requester == current_user,
            Ticket.is_hidden == False
        )\
        .order_by(Ticket.updated_at.desc())\
        .all()

    return render_template('my_tickets.html', tickets=all_tickets)

# Adicione aqui suas rotas de 'manage_categories' e 'delete_category' se você as criou
# ...

if __name__ == '__main__':
    app.run(debug=True)