"""Modelo de dados do núcleo do MVP.

Dados pessoais minimizados (LGPD, LGPD by design): do estudante guardamos só apelido,
série, faixa de idade, escola, bairro/CEP (opcionais) e, para menores, o e-mail do
responsável **cifrado** (Fernet). Nada de nome completo, e-mail do estudante, CPF,
telefone, data de nascimento, nota escolar ou foto (a foto da conta usada pela Visão
é lida em memória e descartada).
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

# Faixa de idade no lugar da data de nascimento. Só "18 ou mais" dispensa o responsável.
FAIXAS_IDADE = ["10 a 12 anos", "13 a 15 anos", "16 ou 17 anos", "18 anos ou mais"]
FAIXA_MAIOR = "18 anos ou mais"

# Consentimento do responsável (LGPD art. 14): menor fica "pendente" até o responsável autorizar pelo link.
# Se o responsável negar, a conta é apagada; não existe estado "negado".
CONSENTIMENTO_PENDENTE = "pendente"
CONSENTIMENTO_AUTORIZADO = "autorizado"
CONSENTIMENTO_NAO_EXIGIDO = "nao_exigido"  # estudante maior de idade

# Canal de chegada do voluntário credenciado no SICREV pelo robô de RPA (UiPath).
ORIGEM_RPA = "rpa_sicrev"

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
    # Nome e e-mail: só voluntário e coordenação (adultos). O estudante entra com apelido e senha.
    nome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, index=True, nullable=True)
    senha_hash: Mapped[str] = mapped_column(String(300))
    papel: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # Versão do Aviso de Privacidade aceita no cadastro e quando.
    aviso_versao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    aviso_aceito_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Estudante
    apelido: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    faixa_idade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    escola_id: Mapped[int | None] = mapped_column(ForeignKey("escolas.id"), nullable=True)
    ano_escolar: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # CEP confirmado pelo estudante (digitado ou lido da conta pela Visão). O endereço completo nunca é gravado.
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    consentimento_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consentimento_responsavel: Mapped[bool] = mapped_column(Boolean, default=False)
    consentimento_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Link de uso único para o responsável: só o hash SHA-256 do token fica no banco.
    consentimento_token_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    consentimento_expira_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # E-mail informado pelo responsável ao autorizar, cifrado com Fernet (chave FERNET_KEY no Key Vault).
    email_responsavel_cifrado: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Canal de chegada: "peca_maker" quando a pessoa veio pelo QR code do suporte do Maker Lab.
    origem: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Voluntário: precisa ser aprovado pela coordenação antes de publicar horários.
    formacao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    aprovado: Mapped[bool] = mapped_column(Boolean, default=True)
    # Opt-in do boletim informado no credenciamento (robô de RPA). None = não informado.
    aceita_boletim: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    escola: Mapped[Escola | None] = relationship()

    @property
    def exibicao(self) -> str:
        """Como a pessoa aparece na tela: apelido do estudante, primeiro nome de adultos."""
        if self.papel == "estudante":
            return self.apelido or "estudante"
        return (self.nome or "").split(" ")[0] or "você"

    @property
    def pode_agendar(self) -> bool:
        return self.papel == "estudante" and self.consentimento_status in (CONSENTIMENTO_AUTORIZADO, CONSENTIMENTO_NAO_EXIGIDO)


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


class Auditoria(Base):
    """Trilha de auditoria: registra a AÇÃO, quem (pseudônimo) e quando, nunca o conteúdo
    (sem apelido, e-mail, dúvida ou dados do formulário)."""

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    acao: Mapped[str] = mapped_column(String(60))
    papel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ator: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quantidade: Mapped[int | None] = mapped_column(Integer, nullable=True)
