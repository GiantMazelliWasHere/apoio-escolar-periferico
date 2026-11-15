"""Modelo de dados do núcleo do MVP.

Dados pessoais minimizados (LGPD): do estudante guardamos só o necessário para
agendar monitorias e medir impacto agregado. Nada de CPF, nota escolar ou foto
(a foto da conta usada pela Visão é lida em memória e descartada).
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# Turnos do filtro de monitorias: (rótulo, hora inicial inclusiva, hora final exclusiva).
TURNOS = {
    "manha": ("Manhã (antes das 12h)", 0, 12),
    "tarde": ("Tarde (12h às 18h)", 12, 18),
    "noite": ("Noite (a partir das 18h)", 18, 24),
}

MATERIAS = [
    "Matemática",
    "Português",
    "Ciências",
    "História",
    "Geografia",
    "Inglês",
    "Física",
    "Química",
    "Biologia",
    "Programação",
]

ANOS_ESCOLARES = [
    "6º ano EF",
    "7º ano EF",
    "8º ano EF",
    "9º ano EF",
    "1ª série EM",
    "2ª série EM",
    "3ª série EM",
]

PAPEIS = ("estudante", "voluntario", "coordenacao")
STATUS_AGENDAMENTO = ("agendado", "realizado", "faltou", "cancelado")


class Escola(Base):
    __tablename__ = "escolas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    bairro: Mapped[str] = mapped_column(String(120))
    municipio: Mapped[str] = mapped_column(String(120))
    # Preenchidos pelo pipeline de Dados (INEP/IBGE). Enquanto o pipeline não
    # chega, o seed usa valores sintéticos e marca a fonte como "sintetico".
    territorio_prioritario: Mapped[bool] = mapped_column(Boolean, default=False)
    indice_prioridade: Mapped[float | None] = mapped_column(Float, nullable=True)
    fonte_prioridade: Mapped[str] = mapped_column(String(40), default="sintetico")
    codigo_inep: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(300))
    papel: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Estudante
    escola_id: Mapped[int | None] = mapped_column(ForeignKey("escolas.id"), nullable=True)
    ano_escolar: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # CEP confirmado pelo estudante (digitado ou lido da conta pela Visão). O endereço completo nunca é gravado.
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    consentimento_responsavel: Mapped[bool] = mapped_column(Boolean, default=False)
    consentimento_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Voluntário
    formacao: Mapped[str | None] = mapped_column(String(200), nullable=True)

    escola: Mapped[Escola | None] = relationship()


class Horario(Base):
    """Horário de monitoria oferecido por um voluntário."""

    __tablename__ = "horarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    voluntario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    materia: Mapped[str] = mapped_column(String(60), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime, index=True)
    duracao_min: Mapped[int] = mapped_column(Integer, default=60)
    modalidade: Mapped[str] = mapped_column(String(20), default="online")
    local_ou_link: Mapped[str] = mapped_column(String(300), default="")
    vagas: Mapped[int] = mapped_column(Integer, default=1)

    voluntario: Mapped[Usuario] = relationship()
    agendamentos: Mapped[list["Agendamento"]] = relationship(back_populates="horario")

    @property
    def vagas_ocupadas(self) -> int:
        return sum(1 for a in self.agendamentos if a.status != "cancelado")

    @property
    def vagas_livres(self) -> int:
        return max(self.vagas - self.vagas_ocupadas, 0)


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    horario_id: Mapped[int] = mapped_column(ForeignKey("horarios.id"))
    estudante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    status: Mapped[str] = mapped_column(String(20), default="agendado")
    duvida: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    horario: Mapped[Horario] = relationship(back_populates="agendamentos")
    estudante: Mapped[Usuario] = relationship()
