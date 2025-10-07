import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Ticket
from ia_service import classify_ticket

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-bem-dificil')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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

        if User.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'warning')
            return redirect(url_for('register'))

        new_user = User(email=email)
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


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        description = request.form.get('description')
        if not description:
            flash('A descrição do chamado não pode estar vazia.', 'warning')
        else:
            categories = [
                # Incidentes
                "Incidente - Hardware",
                "Incidente - Software / Aplicações",
                "Incidente - Rede e Conectividade",
                "Incidente - Contas e Acessos",
                "Incidente - Periféricos",
                "Incidente - Segurança da Informação",
                "Incidente - Facilities / Manutenção Predial",

                # Requisições de Serviço
                "Requisição - Hardware",
                "Requisição - Software / Aplicações",
                "Requisição - Contas e Acessos",
                "Requisição - Periféricos"
            ]

            predicted_category = classify_ticket(description, categories)

            new_ticket = Ticket(
                description=description,
                category=predicted_category,
                author=current_user
            )
            db.session.add(new_ticket)
            db.session.commit()
            flash('Chamado criado e classificado com sucesso!', 'success')
        return redirect(url_for('index'))

    user_tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.id.desc()).all()
    return render_template('index.html', tickets=user_tickets)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)