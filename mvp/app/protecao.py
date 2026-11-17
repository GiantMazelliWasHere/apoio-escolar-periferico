"""Proteções de borda: cabeçalhos de segurança (CSP, HSTS...) e limite de tentativas em login e cadastro."""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Sem scripts de terceiros nem scripts inline: tudo vem de /static.
# style-src-attr libera só o atributo style (barras do painel de impacto usam uma variável CSS).
CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "style-src-attr 'unsafe-inline'",
        "img-src 'self' data:",
        "connect-src 'self'",
        "font-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

# A documentação interativa da API (Swagger) carrega scripts de CDN; fica fora da CSP restrita.
SEM_CSP = ("/api/docs", "/openapi.json")


class CabecalhosSeguranca:
    """Middleware ASGI que acrescenta os cabeçalhos de segurança em todas as respostas."""

    def __init__(self, app: ASGIApp, hsts: bool) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        caminho = scope.get("path", "")

        async def enviar(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                extras = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"same-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=(), payment=()",
                    b"cross-origin-opener-policy": b"same-origin",
                }
                if not caminho.startswith(SEM_CSP):
                    extras[b"content-security-policy"] = CSP.encode()
                if self.hsts:
                    extras[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                existentes = {k.lower() for k, _ in headers}
                headers += [(k, v) for k, v in extras.items() if k not in existentes]
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, enviar)


class LimiteTentativas:
    """Janela deslizante por cliente (IP). Em memória, por processo: suficiente para 1 instância do App Service."""

    def __init__(self, maximo: int, janela_s: int) -> None:
        self.maximo = maximo
        self.janela_s = janela_s
        self._usos: dict[str, deque[float]] = defaultdict(deque)
        self._trava = threading.Lock()

    def registrar(self, cliente: str) -> bool:
        """Conta uma tentativa. Devolve False se o cliente passou do limite."""
        agora = time.monotonic()
        with self._trava:
            fila = self._usos[cliente]
            while fila and agora - fila[0] > self.janela_s:
                fila.popleft()
            if len(fila) >= self.maximo:
                return False
            fila.append(agora)
            return True


def limitar(nome: str):
    """Dependência FastAPI: aplica o limite `request.app.state.limites[nome]` ao IP do cliente."""

    def dep(request: Request) -> None:
        limite: LimiteTentativas = request.app.state.limites[nome]
        cliente = request.client.host if request.client else "desconhecido"
        if not limite.registrar(cliente):
            raise HTTPException(status_code=429, detail="Muitas tentativas seguidas. Espere alguns minutos e tente de novo.")

    return dep
