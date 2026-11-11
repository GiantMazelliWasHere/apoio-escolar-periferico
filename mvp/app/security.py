"""Senhas com hash, proteção CSRF, sessão e controle de acesso por papel."""
import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import Usuario

_ITERACOES = 200_000


def hash_senha(senha: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), _ITERACOES)
    return f"pbkdf2_sha256${_ITERACOES}${salt}${dk.hex()}"


def verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        _, iteracoes, salt, esperado = armazenado.split("$")
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), int(iteracoes))
    return hmac.compare_digest(dk.hex(), esperado)


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


async def csrf_protect(request: Request) -> None:
    form = await request.form()
    enviado = form.get("csrf_token", "")
    esperado = request.session.get("csrf", "")
    if not esperado or not hmac.compare_digest(str(enviado), esperado):
        raise HTTPException(status_code=403, detail="Formulário expirado. Recarregue a página e tente de novo.")


def csrf_header(request: Request) -> None:
    """CSRF para chamadas JSON feitas pelo próprio site (token no cabeçalho X-CSRF-Token)."""
    enviado = request.headers.get("X-CSRF-Token", "")
    esperado = request.session.get("csrf", "")
    if not esperado or not hmac.compare_digest(enviado, esperado):
        raise HTTPException(status_code=403, detail="Sessão expirada. Recarregue a página e tente de novo.")


def usuario_atual(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    uid = request.session.get("uid")
    if uid is None:
        return None
    return db.get(Usuario, uid)


class LoginNecessario(Exception):
    def __init__(self, proximo: str):
        self.proximo = proximo


def exigir_papel(*papeis: str):
    def dep(request: Request, usuario: Usuario | None = Depends(usuario_atual)) -> Usuario:
        if usuario is None:
            raise LoginNecessario(request.url.path)
        if usuario.papel not in papeis:
            raise HTTPException(status_code=403, detail="Esta área é para outro tipo de conta.")
        return usuario

    return dep


def entrar_na_sessao(request: Request, usuario: Usuario) -> None:
    request.session.clear()
    request.session["uid"] = usuario.id
    request.session["csrf"] = secrets.token_urlsafe(32)


def exigir_api_key(request: Request) -> None:
    chave = request.app.state.settings.integration_api_key
    enviada = request.headers.get("X-API-Key", "")
    if not chave or not hmac.compare_digest(enviada, chave):
        raise HTTPException(status_code=401, detail="X-API-Key inválida ou ausente.")
