from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# =========================
# MOTO
# =========================
from datetime import datetime

class Moto(db.Model):

    __tablename__ = "motos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tag_rfid = db.Column(
        db.Integer,
        unique=True,
        nullable=False
    )

    chassi = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    renavam = db.Column(
        db.String(50)
    )

    cor = db.Column(
        db.String(50),
        nullable=False
    )

    ano = db.Column(
        db.String(20),
        nullable=False
    )

    modelo = db.Column(
        db.String(100),
        nullable=False
    )

    placa = db.Column(
        db.String(20)
    )

    montador = db.Column(
        db.String(100)
    )

    local_atual = db.Column(
        db.String(100),
        default="PÁTIO"
    )

    status = db.Column(
        db.String(50),
        default="AGUARDANDO"
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.now,
        nullable=False
    )
# =========================
# PONTOS RFID
# =========================
class PontoRFID(db.Model):

    __tablename__ = 'pontos_rfid'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )


# =========================
# LEITURAS RFID
# =========================
class Leitura(db.Model):

    __tablename__ = 'leituras'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tag_rfid = db.Column(
        db.String(100),
        nullable=False
    )

    setor = db.Column(
        db.String(100),
        nullable=False
    )

    data_hora = db.Column(
        db.String(100),
        nullable=False
    )


# =========================
# HISTÓRICO DE MOTOS
# =========================
class HistoricoMoto(db.Model):

    __tablename__ = "historico_motos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tag_rfid = db.Column(
        db.String(100)
    )

    chassi = db.Column(
        db.String(100)
    )

    modelo = db.Column(
        db.String(100)
    )

    cor = db.Column(
        db.String(50)
    )

    ano = db.Column(
        db.String(10)
    )

    placa = db.Column(
        db.String(20)
    )

    montador = db.Column(
        db.String(100)
    )

    data_entrega = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# =========================
# MOTOS IMPORTADAS DO CSV
# =========================
class MotoImportada(db.Model):

    __tablename__ = "motos_importadas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    chassi = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    modelo = db.Column(
        db.String(100),
        nullable=False
    )

    cor = db.Column(
        db.String(50),
        nullable=False
    )

    ano = db.Column(
        db.String(10),
        nullable=False
    )