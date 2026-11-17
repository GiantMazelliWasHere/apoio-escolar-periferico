"""Proteção de dados de menores (LGPD by design).

- Consentimento do responsável (art. 14): link de uso único, guardado só como hash, válido por 30 dias.
  O estudante manda o link ao responsável (WhatsApp ou como preferir). Sem resposta em 30 dias, a conta é apagada.
- E-mail do responsável cifrado em repouso (Fernet, chave FERNET_KEY no Key Vault).
- Direitos do titular (art. 18): baixar os próprios dados e apagar a conta.
- Auditoria: registra a ação, nunca o conteúdo.
- Indicadores agregados: grupos com menos de K_MINIMO pessoas não aparecem.
"""
import base64
import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import (
    CONSENTIMENTO_AUTORIZADO,
    CONSENTIMENTO_PENDENTE,
    Agendamento,
    Auditoria,
    Horario,
    Usuario,
)

log = logging.getLogger("apoio")

# Versão do Aviso de Privacidade (/privacidade). Mudou o texto? Atualize a versão e a data.
AVISO_VERSAO = "2.0"
AVISO_DATA = "18/11/2026"

PRAZO_CONSENTIMENTO = timedelta(days=30)
K_MINIMO = 5  # grupos menores que isso ficam ocultos nos indicadores

APELIDO_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,19}$")


def normalizar_apelido(apelido: str) -> str:
    return (apelido or "").strip().lower()


def apelido_valido(apelido: str) -> bool:
    return bool(APELIDO_RE.fullmatch(apelido))


# ---------- Cifra ----------


class Cifra:
    """Fernet (AES-128-CBC + HMAC-SHA256). Em produção a chave vem do Key Vault (FERNET_KEY)."""

    def __init__(self, chave: str) -> None:
        self._fernet = Fernet(chave.encode() if isinstance(chave, str) else chave)

    @staticmethod
    def chave_de_desenvolvimento(segredo: str) -> str:
        """Deriva uma chave válida de outro segredo (só fora de produção, onde FERNET_KEY é opcional)."""
        return base64.urlsafe_b64encode(hashlib.sha256(f"fernet:{segredo}".encode()).digest()).decode()

    def cifrar(self, texto: str) -> str:
        return self._fernet.encrypt(texto.encode()).decode()

    def decifrar(self, token: str | None) -> str | None:
        if not token:
            return None
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            log.warning("Não foi possível decifrar um campo (chave trocada?)")
            return None


# ---------- Link do responsável ----------


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def gerar_link_responsavel(usuario: Usuario, agora: datetime | None = None) -> str:
    """Gera (ou regera) o token de uso único. Devolve o token em claro, que não é guardado."""
    agora = agora or datetime.now()
    token = secrets.token_urlsafe(32)
    usuario.consentimento_token_hash = hash_token(token)
    # O prazo conta do cadastro: gerar um link novo não estende os 30 dias.
    usuario.consentimento_expira_em = (usuario.criado_em or agora) + PRAZO_CONSENTIMENTO
    return token


def buscar_por_token(db: Session, token: str, agora: datetime | None = None) -> Usuario | None:
    agora = agora or datetime.now()
    if not token or len(token) > 100:
        return None
    u = db.scalar(select(Usuario).where(Usuario.consentimento_token_hash == hash_token(token)))
    if u is None or u.consentimento_status != CONSENTIMENTO_PENDENTE:
        return None
    if u.consentimento_expira_em and u.consentimento_expira_em < agora:
        return None
    return u


def autorizar(db: Session, usuario: Usuario, email_responsavel: str, cifra: Cifra, agora: datetime | None = None) -> None:
    agora = agora or datetime.now()
    usuario.consentimento_status = CONSENTIMENTO_AUTORIZADO
    usuario.consentimento_responsavel = True
    usuario.consentimento_em = agora
    usuario.email_responsavel_cifrado = cifra.cifrar(email_responsavel.strip().lower())
    usuario.consentimento_token_hash = None  # uso único
    usuario.consentimento_expira_em = None


# ---------- Apagar, expurgar e exportar ----------


def apagar_usuario(db: Session, usuario: Usuario) -> None:
    """Apaga a conta e tudo o que depende dela (agendamentos; horários do voluntário)."""
    if usuario.papel == "voluntario":
        ids_horarios = select(Horario.id).where(Horario.voluntario_id == usuario.id)
        db.execute(delete(Agendamento).where(Agendamento.horario_id.in_(ids_horarios)))
        db.execute(delete(Horario).where(Horario.voluntario_id == usuario.id))
    db.execute(delete(Agendamento).where(Agendamento.estudante_id == usuario.id))
    db.delete(usuario)


def expurgar_pendentes(db: Session, agora: datetime | None = None) -> int:
    """Apaga cadastros de menores sem autorização do responsável depois de 30 dias."""
    agora = agora or datetime.now()
    vencidos = db.scalars(
        select(Usuario).where(
            Usuario.papel == "estudante",
            Usuario.consentimento_status == CONSENTIMENTO_PENDENTE,
            Usuario.criado_em < agora - PRAZO_CONSENTIMENTO,
        )
    ).all()
    for u in vencidos:
        apagar_usuario(db, u)
    if vencidos:
        auditar(db, "expurgo_cadastros_sem_autorizacao", quantidade=len(vencidos))
    db.commit()
    return len(vencidos)


def _iso(d: datetime | None) -> str | None:
    return d.isoformat(timespec="seconds") if d else None


def exportar_dados(db: Session, usuario: Usuario, cifra: Cifra) -> dict:
    """Tudo o que a plataforma guarda sobre a conta (sem o hash da senha nem o hash do link)."""
    conta = {
        "papel": usuario.papel,
        "criado_em": _iso(usuario.criado_em),
        "aviso_de_privacidade": {"versao": usuario.aviso_versao, "aceito_em": _iso(usuario.aviso_aceito_em)},
        "origem": usuario.origem,
    }
    dados: dict = {"exportado_em": _iso(datetime.now()), "conta": conta}
    if usuario.papel == "estudante":
        conta.update(
            apelido=usuario.apelido,
            faixa_idade=usuario.faixa_idade,
            escola=usuario.escola.nome if usuario.escola else None,
            ano_escolar=usuario.ano_escolar,
            bairro=usuario.bairro,
            cep=usuario.cep,
            consentimento={
                "status": usuario.consentimento_status,
                "autorizado_em": _iso(usuario.consentimento_em),
                "email_do_responsavel": cifra.decifrar(usuario.email_responsavel_cifrado),
            },
        )
        ags = db.scalars(select(Agendamento).where(Agendamento.estudante_id == usuario.id).order_by(Agendamento.id)).all()
        dados["agendamentos"] = [
            {
                "materia": a.horario.materia,
                "inicio": _iso(a.horario.inicio),
                "monitor": (a.horario.voluntario.nome or "") if a.horario.voluntario else None,
                "status": a.status,
                "duvida": a.duvida,
                "criado_em": _iso(a.criado_em),
            }
            for a in ags
        ]
    else:
        conta.update(nome=usuario.nome, email=usuario.email, formacao=usuario.formacao, aprovado=usuario.aprovado)
        if usuario.papel == "voluntario" and (usuario.apelido or usuario.aceita_boletim is not None):
            conta.update(apelido=usuario.apelido, bairro=usuario.bairro, aceita_boletim=usuario.aceita_boletim)
        if usuario.papel == "voluntario":
            hs = db.scalars(select(Horario).where(Horario.voluntario_id == usuario.id).order_by(Horario.inicio)).all()
            dados["horarios"] = [
                {
                    "materia": h.materia,
                    "inicio": _iso(h.inicio),
                    "duracao_min": h.duracao_min,
                    "modalidade": h.modalidade,
                    "local_ou_link": h.local_ou_link,
                    "vagas": h.vagas,
                }
                for h in hs
            ]
    return dados


# ---------- Auditoria ----------

_SAL_AUDITORIA = {"valor": ""}


def configurar_auditoria(segredo: str) -> None:
    _SAL_AUDITORIA["valor"] = segredo


def pseudonimo(uid: int | None) -> str | None:
    """Identificador estável e não reversível sem o segredo (HMAC do id)."""
    if uid is None:
        return None
    return hmac.new(_SAL_AUDITORIA["valor"].encode(), str(uid).encode(), hashlib.sha256).hexdigest()[:12]


def auditar(db: Session, acao: str, usuario: Usuario | None = None, quantidade: int | None = None) -> None:
    db.add(
        Auditoria(
            acao=acao,
            papel=usuario.papel if usuario else None,
            ator=pseudonimo(usuario.id) if usuario else None,
            quantidade=quantidade,
        )
    )
    log.info("auditoria: %s", acao)  # só a ação, nunca dados da pessoa


# ---------- Indicadores com supressão de grupos pequenos ----------


def suprimir(n: int | None) -> int | None:
    """Contagens de pessoas entre 1 e K_MINIMO - 1 viram None ("menos de 5")."""
    if n is None:
        return None
    return n if n == 0 or n >= K_MINIMO else None
