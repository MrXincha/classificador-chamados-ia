from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    employee_code = db.Column(db.String(50), nullable=True, unique=True)

    tickets = db.relationship('Ticket', backref='requester', lazy=True, foreign_keys='Ticket.user_id')
    comments = db.relationship('TicketComment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    tickets = db.relationship('Ticket', backref='category_obj', lazy=True)
    kb_items = db.relationship('KnowledgeBaseItem', backref='category_obj', lazy=True)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Aberto')
    priority = db.Column(db.String(50), nullable=False, default='Média')
    ticket_type = db.Column(db.String(50), nullable=False, default='Incidente')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)
    responsible_name = db.Column(db.String(100), nullable=True, default="Aguardando Triagem")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)
    comments = db.relationship('TicketComment', backref='ticket', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='ticket', lazy=True, cascade="all, delete-orphan")

class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class KnowledgeBaseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keywords = db.Column(db.String(500), nullable=False)
    solution_text = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Nome do arquivo como salvo no servidor (ex: 8sd9f8sd9f.pdf)
    storage_filename = db.Column(db.String(300), nullable=False)

    # Nome original do arquivo (ex: "print_do_erro.png")
    original_filename = db.Column(db.String(300), nullable=False)

    uploaded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))