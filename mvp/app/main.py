"""Núcleo do MVP — Apoio Escolar Periférico.

Fluxo central: cadastro do estudante → busca de monitoria por matéria →
agendamento → voluntário registra presença → painel de impacto.
"""
import asyncio
import csv
import hashlib
import io
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload
from starlette.middleware.sessions import SessionMiddleware

from .assistente import FAQ, MAX_PERGUNTA, NOME_ASSISTENTE, Assistente, LimiteExcedido, criar_chamada_openrouter
from .config import Settings
from .db import Base, adicionar_colunas_novas, get_db, make_sessionmaker
from .kpis import calcular_impacto
from .lgpd import (
    AVISO_DATA,
    AVISO_VERSAO,
    Cifra,
    apagar_usuario,
    apelido_valido,
    auditar,
    autorizar,
    buscar_por_token,
    configurar_auditoria,
    exportar_dados,
    expurgar_pendentes,
    gerar_link_responsavel,
    normalizar_apelido,
)
from .maker import ORIGEM_MAKER, ORIGENS_VALIDAS, PECA, qr_svg, url_do_qr
from .models import (
    ANOS_ESCOLARES,
    CONSENTIMENTO_NAO_EXIGIDO,
    CONSENTIMENTO_PENDENTE,
    FAIXA_MAIOR,
    FAIXAS_IDADE,
    MATERIAS,
    ORIGEM_RPA,
    TURNOS,
    Agendamento,
    Escola,
    Horario,
    Usuario,
)
from .protecao import CabecalhosSeguranca, LimiteTentativas, limitar
from .security import (
    LoginNecessario,
    csrf_header,
    csrf_protect,
    csrf_token,
    entrar_na_sessao,
    exigir_api_key,
    exigir_papel,
    hash_senha,
    usuario_atual,
    verificar_senha,
)
from .seed import seed_demo
from .telemetria import configurar_telemetria
from .visao import MAX_BYTES, TIPOS_ACEITOS, ArquivoInvalido, LeitorEndereco, criar_ocr_easyocr
from .visao import LimiteExcedido as LimiteVisao

BASE_DIR = Path(__file__).parent
log = logging.getLogger("apoio")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

INTERVALO_EXPURGO_S = 60 * 60  # verifica cadastros sem autorização a cada hora
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
JANELA_PRESENCA = timedelta(hours=1)  # presença só perto do horário: evita inflar indicadores
STATUS_LABEL = {"agendado": "Agendada", "realizado": "Realizada", "faltou": "Falta", "cancelado": "Cancelada"}
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def data_amigavel(d: datetime) -> str:
    return f"{DIAS[d.weekday()]}, {d:%d/%m} às {d:%H:%M}"


def horas_minutos(total_min: int) -> str:
    h, m = divmod(int(total_min), 60)
    return f"{h} h {m} min" if m else f"{h} h"


def monitorias_realizadas(horarios) -> list[Horario]:
    """Sessões que contam horas para o voluntário: horários passados com ao menos uma presença confirmada.
    Uma sessão com vários estudantes conta uma vez (é o tempo do voluntário)."""
    return [h for h in horarios if any(a.status == "realizado" for a in h.agendamentos)]


MAX_HORARIOS_POR_ENVIO = 40


templates.env.filters["data_amigavel"] = data_amigavel
templates.env.filters["horas_minutos"] = horas_minutos
templates.env.globals["DIAS"] = DIAS
templates.env.globals["STATUS_LABEL"] = STATUS_LABEL


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def destino_do_papel(usuario: Usuario) -> str:
    return {"estudante": "/monitorias", "voluntario": "/voluntario", "coordenacao": "/impacto"}[usuario.papel]


class PrioridadeEscola(BaseModel):
    escola_id: int | None = None
    codigo_inep: str | None = None
    territorio_prioritario: bool
    indice_prioridade: float | None = None


# RPA → núcleo: voluntários credenciados no SICREV pelo robô (contrato em docs/INTEGRACAO.md).
APELIDO_RPA_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
MAX_LOTE_RPA = 500


class VoluntarioRPA(BaseModel):
    """Mínimo necessário (LGPD): sem CPF, nome ou telefone. Campo extra é recusado."""

    model_config = {"extra": "forbid"}

    apelido: str = Field(max_length=30)
    email: str = Field(max_length=200)
    bairro: str = Field(default="", max_length=120)
    aceita_boletim: bool = False

    @field_validator("apelido")
    @classmethod
    def _apelido(cls, v: str) -> str:
        v = v.strip()
        if not APELIDO_RPA_RE.fullmatch(v):
            raise ValueError("apelido inválido (3 a 30 caracteres: letras, números, _ . -)")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.fullmatch(v):
            raise ValueError("e-mail inválido")
        return v


class PerguntaAssistente(BaseModel):
    pergunta: str = Field(max_length=MAX_PERGUNTA)

    @field_validator("pergunta")
    @classmethod
    def _nao_vazia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Escreva a sua dúvida.")
        return v


def origem_da_sessao(request: Request) -> str | None:
    """Canal de chegada marcado na sessão (ex.: QR code da peça do Maker Lab), se for um valor conhecido."""
    origem = request.session.get("origem")
    return origem if origem in ORIGENS_VALIDAS else None


def normalizar_cep(cep: str) -> str | None:
    """"01234567", "01234-567" ou "01.234-567" → "01234-567". Vazio → None. Inválido → ValueError."""
    digitos = re.sub(r"\D", "", cep or "")
    if not digitos:
        return None
    if len(digitos) != 8:
        raise ValueError(cep)
    return f"{digitos[:5]}-{digitos[5:]}"


def rodar_expurgo(app: FastAPI) -> int:
    with app.state.SessionLocal() as db:
        return expurgar_pendentes(db)


async def _expurgo_periodico(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(INTERVALO_EXPURGO_S)
        try:
            await run_in_threadpool(rodar_expurgo, app)
        except Exception:
            log.exception("Falha no expurgo periódico")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    tarefa = asyncio.create_task(_expurgo_periodico(app))
    try:
        yield
    finally:
        tarefa.cancel()


def create_app(database_url: str | None = None, seed: bool | None = None) -> FastAPI:
    settings = Settings()
    app = FastAPI(title="Apoio Escolar Periférico — MVP", docs_url="/api/docs", redoc_url=None, lifespan=ciclo_de_vida)
    app.state.settings = settings
    configurar_telemetria(app)
    configurar_auditoria(settings.secret_key)
    app.state.cifra = Cifra(settings.fernet_key or Cifra.chave_de_desenvolvimento(settings.secret_key))
    # Login: 10 tentativas por IP a cada 5 min; cadastros e link do responsável: limites por hora.
    app.state.limites = {
        "login": LimiteTentativas(10, 5 * 60),
        "cadastro": LimiteTentativas(10, 60 * 60),
        "responsavel": LimiteTentativas(20, 60 * 60),
    }
    app.state.SessionLocal = make_sessionmaker(database_url or settings.database_url)

    app.state.assistente = Assistente(
        criar_chamada_openrouter(settings.openrouter_api_key, settings.genai_model) if settings.openrouter_api_key else None
    )

    app.state.visao = LeitorEndereco(criar_ocr_easyocr())

    engine = app.state.SessionLocal.kw["bind"]
    Base.metadata.create_all(engine)
    adicionar_colunas_novas(engine)
    if settings.seed_demo if seed is None else seed:
        with app.state.SessionLocal() as db:
            seed_demo(db)
    rodar_expurgo(app)  # cadastros vencidos enquanto o app estava parado

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="aep_sessao",
        same_site="lax",
        https_only=settings.https_only_cookies,
        max_age=60 * 60 * 8,
    )
    app.add_middleware(CabecalhosSeguranca, hsts=settings.env == "production")
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    def render(request: Request, nome: str, usuario: Usuario | None, status_code: int = 200, **ctx) -> HTMLResponse:
        ctx.update(usuario=usuario, csrf_token=csrf_token(request), demo=True, aviso_versao=AVISO_VERSAO, aviso_data=AVISO_DATA)
        return templates.TemplateResponse(request, nome, ctx, status_code=status_code)

    @app.exception_handler(LoginNecessario)
    async def _login(request: Request, exc: LoginNecessario):
        return redirect(f"/entrar?proximo={exc.proximo}")

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        return templates.TemplateResponse(
            request, "erro.html", {"mensagem": exc.detail, "usuario": None, "csrf_token": csrf_token(request), "demo": True}, status_code=exc.status_code
        )

    # ---------- Páginas públicas ----------

    @app.get("/health")
    def health():
        """Sondado pelo App Service (Health check) e pelo smoke test do deploy: testa o banco e informa a versão."""
        try:
            with app.state.SessionLocal() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            log.exception("Health check: banco indisponível")
            return JSONResponse({"status": "erro", "banco": "erro", "versao": settings.versao}, status_code=503)
        return {"status": "ok", "banco": "ok", "versao": settings.versao}

    @app.get("/", response_class=HTMLResponse)
    def inicio(request: Request, conta_apagada: int = 0, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "index.html", usuario, materias=MATERIAS, veio_da_peca=request.session.get("origem") in ORIGENS_VALIDAS, conta_apagada=conta_apagada)

    # ---------- Maker Lab: QR code da peça física ----------

    def base_publica(request: Request) -> str:
        return request.app.state.settings.public_url or str(request.base_url).rstrip("/")

    @app.get("/qr")
    def qr_da_peca(request: Request):
        """Destino do QR code do suporte de tablet. Marca a origem na sessão e leva ao início."""
        if "uid" not in request.session:
            request.session["origem"] = ORIGEM_MAKER
        return redirect("/")

    @app.get("/maker", response_class=HTMLResponse)
    def pagina_maker(request: Request, db: Session = Depends(get_db), usuario: Usuario | None = Depends(usuario_atual)):
        destino = url_do_qr(base_publica(request))
        k = calcular_impacto(db)
        return render(request, "maker.html", usuario, peca=PECA, destino=destino, qr=qr_svg(destino), cadastros=k["cadastros_via_peca_maker"])

    @app.get("/maker/qrcode.svg")
    def qrcode_svg(request: Request, tamanho_mm: int = PECA["etiqueta_mm"]):
        """QR vetorial no tamanho da etiqueta (padrão: PECA["etiqueta_mm"]), para imprimir em papel adesivo."""
        tamanho_mm = min(max(tamanho_mm, 15), 200)
        svg = qr_svg(url_do_qr(base_publica(request)), tamanho_mm=tamanho_mm)
        return PlainTextResponse(
            svg,
            media_type="image/svg+xml",
            headers={"Content-Disposition": 'inline; filename="qrcode_suporte_tablet.svg"'},
        )

    @app.get("/privacidade", response_class=HTMLResponse)
    def privacidade(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "privacidade.html", usuario, regiao=settings.regiao)

    @app.get("/ajuda", response_class=HTMLResponse)
    def ajuda(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "ajuda.html", usuario, faq=FAQ, assistente=NOME_ASSISTENTE, ia_ativa=request.app.state.assistente.ativo, max_pergunta=MAX_PERGUNTA)

    # ---------- Autenticação ----------

    @app.get("/entrar", response_class=HTMLResponse)
    def entrar_form(request: Request, proximo: str = "", usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "entrar.html", usuario, proximo=proximo)

    @app.post("/entrar", dependencies=[Depends(csrf_protect), Depends(limitar("login"))])
    def entrar(request: Request, login: str = Form(...), senha: str = Form(...), proximo: str = Form(""), db: Session = Depends(get_db)):
        """Estudante entra com o apelido; voluntário e coordenação, com o e-mail."""
        login = login.strip().lower()
        campo = Usuario.email if "@" in login else Usuario.apelido
        u = db.scalar(select(Usuario).where(campo == login))
        if u is None or not verificar_senha(senha, u.senha_hash):
            return render(request, "entrar.html", None, status_code=400, erro="Apelido/e-mail ou senha incorretos.", proximo=proximo)
        entrar_na_sessao(request, u)
        destino = proximo if proximo.startswith("/") and not proximo.startswith("//") else destino_do_papel(u)
        return redirect(destino)

    @app.post("/sair", dependencies=[Depends(csrf_protect)])
    def sair(request: Request):
        request.session.clear()
        return redirect("/")

    @app.get("/cadastro/estudante", response_class=HTMLResponse)
    def cadastro_estudante_form(request: Request, db: Session = Depends(get_db), usuario: Usuario | None = Depends(usuario_atual)):
        escolas = db.scalars(select(Escola).order_by(Escola.nome)).all()
        return render(request, "cadastro_estudante.html", usuario, escolas=escolas, anos=ANOS_ESCOLARES, faixas=FAIXAS_IDADE, form={}, visao_ativa=request.app.state.visao.ativo)

    @app.post("/cadastro/estudante", dependencies=[Depends(csrf_protect), Depends(limitar("cadastro"))])
    def cadastro_estudante(
        request: Request,
        apelido: str = Form(...),
        senha: str = Form(...),
        escola_id: int = Form(...),
        ano_escolar: str = Form(...),
        faixa_idade: str = Form(...),
        bairro: str = Form(""),
        cep: str = Form(""),
        aceite_aviso: str | None = Form(None),
        db: Session = Depends(get_db),
    ):
        apelido = normalizar_apelido(apelido)
        form = {"apelido": apelido, "escola_id": escola_id, "ano_escolar": ano_escolar, "faixa_idade": faixa_idade, "bairro": bairro, "cep": cep}
        erro = None
        try:
            cep_ok = normalizar_cep(cep)
        except ValueError:
            cep_ok = None
        if not apelido_valido(apelido):
            erro = "O apelido precisa ter de 3 a 20 caracteres: letras sem acento, números, ponto, hífen ou _. Não use seu nome completo."
        elif len(senha) < 8:
            erro = "A senha precisa ter pelo menos 8 caracteres."
        elif db.scalar(select(Usuario).where(Usuario.apelido == apelido)):
            erro = "Este apelido já está em uso. Escolha outro."
        elif db.get(Escola, escola_id) is None or ano_escolar not in ANOS_ESCOLARES or faixa_idade not in FAIXAS_IDADE:
            erro = "Escolha a escola, o ano escolar e a faixa de idade da lista."
        elif cep.strip() and cep_ok is None:
            erro = "O CEP precisa ter 8 números (ex.: 08250-000). Se não souber, deixe em branco."
        elif not aceite_aviso:
            erro = "Para criar a conta, leia e aceite o Aviso de Privacidade."
        if erro:
            escolas = db.scalars(select(Escola).order_by(Escola.nome)).all()
            return render(request, "cadastro_estudante.html", None, status_code=400, erro=erro, escolas=escolas, anos=ANOS_ESCOLARES, faixas=FAIXAS_IDADE, form=form, visao_ativa=request.app.state.visao.ativo)
        agora = datetime.now()
        menor = faixa_idade != FAIXA_MAIOR
        u = Usuario(
            apelido=apelido,
            senha_hash=hash_senha(senha),
            papel="estudante",
            faixa_idade=faixa_idade,
            escola_id=escola_id,
            ano_escolar=ano_escolar,
            bairro=bairro.strip()[:120] or None,
            cep=cep_ok,
            consentimento_status=CONSENTIMENTO_PENDENTE if menor else CONSENTIMENTO_NAO_EXIGIDO,
            aviso_versao=AVISO_VERSAO,
            aviso_aceito_em=agora,
            origem=origem_da_sessao(request),
            criado_em=agora,
        )
        token = gerar_link_responsavel(u, agora) if menor else None
        db.add(u)
        db.flush()
        auditar(db, "cadastro_estudante", u)
        db.commit()
        entrar_na_sessao(request, u)
        if token:
            return render(request, "link_responsavel.html", u, link=link_responsavel(request, token), novo_cadastro=True)
        return redirect("/monitorias?bemvindo=1")

    def link_responsavel(request: Request, token: str) -> str:
        base = request.app.state.settings.public_url or str(request.base_url).rstrip("/")
        return f"{base}/responsavel/{token}"

    @app.get("/minha-conta/responsavel", response_class=HTMLResponse)
    def link_responsavel_form(request: Request, usuario: Usuario = Depends(exigir_papel("estudante"))):
        if usuario.consentimento_status != CONSENTIMENTO_PENDENTE:
            return redirect("/minha-conta")
        return render(request, "link_responsavel.html", usuario, link=None)

    @app.post("/minha-conta/responsavel", dependencies=[Depends(csrf_protect)])
    def novo_link_responsavel(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("estudante"))):
        """Gera um link novo (o anterior deixa de valer). O prazo de 30 dias continua contando do cadastro."""
        if usuario.consentimento_status != CONSENTIMENTO_PENDENTE:
            return redirect("/minha-conta")
        token = gerar_link_responsavel(usuario)
        auditar(db, "link_responsavel_gerado", usuario)
        db.commit()
        return render(request, "link_responsavel.html", usuario, link=link_responsavel(request, token))

    # ---------- Responsável (sem login: o link de uso único é a credencial) ----------

    @app.get("/responsavel/{token}", response_class=HTMLResponse, dependencies=[Depends(limitar("responsavel"))])
    def responsavel_form(request: Request, token: str, db: Session = Depends(get_db)):
        u = buscar_por_token(db, token)
        if u is None:
            return render(request, "responsavel.html", None, status_code=404, invalido=True)
        return render(request, "responsavel.html", None, estudante=u, token=token)

    @app.post("/responsavel/{token}", dependencies=[Depends(csrf_protect), Depends(limitar("responsavel"))])
    def responsavel_decidir(
        request: Request,
        token: str,
        decisao: str = Form(...),
        email_responsavel: str = Form(""),
        declaro: str | None = Form(None),
        db: Session = Depends(get_db),
    ):
        u = buscar_por_token(db, token)
        if u is None:
            return render(request, "responsavel.html", None, status_code=404, invalido=True)
        if decisao == "negar":
            apagar_usuario(db, u)
            auditar(db, "consentimento_negado_cadastro_apagado")
            db.commit()
            return render(request, "responsavel.html", None, concluido="negado")
        if decisao != "autorizar":
            raise HTTPException(400, "Escolha autorizar ou não autorizar.")
        email_responsavel = email_responsavel.strip()
        if not EMAIL_RE.fullmatch(email_responsavel) or len(email_responsavel) > 200 or not declaro:
            return render(
                request, "responsavel.html", None, status_code=400, estudante=u, token=token,
                erro="Informe um e-mail válido e confirme que você é o responsável legal.",
            )
        autorizar(db, u, email_responsavel, request.app.state.cifra)
        auditar(db, "consentimento_autorizado", u)
        db.commit()
        return render(request, "responsavel.html", None, concluido="autorizado")

    # ---------- Minha conta: direitos do titular (LGPD art. 18) ----------

    @app.get("/minha-conta", response_class=HTMLResponse)
    def minha_conta(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        if usuario is None:
            raise LoginNecessario("/minha-conta")
        return render(request, "minha_conta.html", usuario, faixa_maior=FAIXA_MAIOR)

    @app.get("/minha-conta/dados.json")
    def meus_dados(request: Request, db: Session = Depends(get_db), usuario: Usuario | None = Depends(usuario_atual)):
        if usuario is None:
            raise LoginNecessario("/minha-conta")
        dados = exportar_dados(db, usuario, request.app.state.cifra)
        auditar(db, "dados_exportados", usuario)
        db.commit()
        return JSONResponse(dados, headers={"Content-Disposition": 'attachment; filename="meus-dados-apoio-escolar.json"', "Cache-Control": "no-store"})

    @app.post("/minha-conta/apagar", dependencies=[Depends(csrf_protect)])
    def apagar_conta(request: Request, senha: str = Form(...), db: Session = Depends(get_db), usuario: Usuario | None = Depends(usuario_atual)):
        if usuario is None:
            raise LoginNecessario("/minha-conta")
        if usuario.papel == "coordenacao":
            raise HTTPException(400, "Conta da coordenação é removida pela equipe do projeto.")
        if not verificar_senha(senha, usuario.senha_hash):
            return render(request, "minha_conta.html", usuario, status_code=400, faixa_maior=FAIXA_MAIOR, erro="Senha incorreta. A conta não foi apagada.")
        auditar(db, "conta_apagada_pelo_titular", usuario)
        apagar_usuario(db, usuario)
        db.commit()
        request.session.clear()
        return redirect("/?conta_apagada=1")

    @app.get("/cadastro/voluntario", response_class=HTMLResponse)
    def cadastro_voluntario_form(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "cadastro_voluntario.html", usuario, form={})

    @app.post("/cadastro/voluntario", dependencies=[Depends(csrf_protect), Depends(limitar("cadastro"))])
    def cadastro_voluntario(
        request: Request,
        nome: str = Form(...),
        email: str = Form(...),
        senha: str = Form(...),
        formacao: str = Form(""),
        aceite_aviso: str | None = Form(None),
        db: Session = Depends(get_db),
    ):
        email = email.strip().lower()
        erro = None
        if not nome.strip() or not EMAIL_RE.fullmatch(email):
            erro = "Informe seu nome e um e-mail válido."
        elif len(senha) < 8:
            erro = "A senha precisa ter pelo menos 8 caracteres."
        elif db.scalar(select(Usuario).where(Usuario.email == email)):
            erro = "Este e-mail já tem cadastro. Use \"Entrar\"."
        elif not aceite_aviso:
            erro = "Para criar a conta, leia e aceite o Aviso de Privacidade."
        if erro:
            return render(request, "cadastro_voluntario.html", None, status_code=400, erro=erro, form={"nome": nome, "email": email, "formacao": formacao})
        u = Usuario(
            nome=nome.strip()[:120],
            email=email,
            senha_hash=hash_senha(senha),
            papel="voluntario",
            formacao=formacao.strip()[:200] or None,
            origem=origem_da_sessao(request),
            aprovado=False,  # a coordenação aprova antes de o voluntário ver estudantes
            aviso_versao=AVISO_VERSAO,
            aviso_aceito_em=datetime.now(),
        )
        db.add(u)
        db.flush()
        auditar(db, "cadastro_voluntario", u)
        db.commit()
        entrar_na_sessao(request, u)
        return redirect("/voluntario?bemvindo=1")

    # ---------- Estudante ----------

    @app.get("/monitorias", response_class=HTMLResponse)
    def monitorias(request: Request, materia: str = "", turno: str = "", bemvindo: int = 0, db: Session = Depends(get_db), usuario: Usuario | None = Depends(usuario_atual)):
        q = (
            select(Horario)
            .options(selectinload(Horario.agendamentos), selectinload(Horario.voluntario))
            .where(Horario.inicio > datetime.now())
            .order_by(Horario.inicio)
        )
        if materia in MATERIAS:
            q = q.where(Horario.materia == materia)
        if turno not in TURNOS:
            turno = ""
        horarios = [h for h in db.scalars(q).all() if h.vagas_livres > 0]
        if turno:
            _, hora_ini, hora_fim = TURNOS[turno]
            horarios = [h for h in horarios if hora_ini <= h.inicio.hour < hora_fim]
        horarios = horarios[:30]
        ja_agendados = set()
        if usuario and usuario.papel == "estudante":
            ja_agendados = set(
                db.scalars(select(Agendamento.horario_id).where(Agendamento.estudante_id == usuario.id, Agendamento.status != "cancelado")).all()
            )
        return render(request, "monitorias.html", usuario, horarios=horarios, materias=MATERIAS, materia=materia, turnos=TURNOS, turno=turno, bemvindo=bemvindo, ja_agendados=ja_agendados)

    @app.post("/monitorias/{horario_id}/agendar", dependencies=[Depends(csrf_protect)])
    def agendar(
        horario_id: int,
        duvida: str = Form(""),
        db: Session = Depends(get_db),
        usuario: Usuario = Depends(exigir_papel("estudante")),
    ):
        if not usuario.pode_agendar:
            raise HTTPException(403, "Sua conta está esperando a autorização do seu responsável. Envie o link em \"Minha conta\".")
        h = db.get(Horario, horario_id)
        if h is None or h.inicio <= datetime.now():
            raise HTTPException(404, "Este horário não está mais disponível.")
        if any(a.estudante_id == usuario.id and a.status != "cancelado" for a in h.agendamentos):
            raise HTTPException(409, "Você já agendou este horário.")
        if h.vagas_livres <= 0:
            raise HTTPException(409, "Este horário acabou de lotar. Escolha outro.")
        ag = Agendamento(horario_id=h.id, estudante_id=usuario.id, duvida=duvida.strip()[:500] or None)
        db.add(ag)
        db.commit()
        return redirect(f"/agendamentos/{ag.id}/confirmado")

    @app.get("/agendamentos/{ag_id}/confirmado", response_class=HTMLResponse)
    def confirmado(request: Request, ag_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("estudante"))):
        ag = db.get(Agendamento, ag_id)
        if ag is None or ag.estudante_id != usuario.id:
            raise HTTPException(404, "Agendamento não encontrado.")
        return render(request, "confirmado.html", usuario, ag=ag)

    @app.get("/minhas-monitorias", response_class=HTMLResponse)
    def minhas(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("estudante"))):
        ags = db.scalars(
            select(Agendamento)
            .join(Horario)
            .options(selectinload(Agendamento.horario).selectinload(Horario.voluntario))
            .where(Agendamento.estudante_id == usuario.id)
            .order_by(Horario.inicio.desc())
        ).all()
        agora = datetime.now()
        return render(request, "minhas.html", usuario, proximas=[a for a in ags if a.horario.inicio > agora and a.status == "agendado"], historico=[a for a in ags if not (a.horario.inicio > agora and a.status == "agendado")])

    @app.post("/agendamentos/{ag_id}/cancelar", dependencies=[Depends(csrf_protect)])
    def cancelar(ag_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("estudante"))):
        ag = db.get(Agendamento, ag_id)
        if ag is None or ag.estudante_id != usuario.id or ag.status != "agendado":
            raise HTTPException(404, "Agendamento não encontrado.")
        ag.status = "cancelado"
        db.commit()
        return redirect("/minhas-monitorias")

    # ---------- Voluntário ----------

    @app.get("/voluntario", response_class=HTMLResponse)
    def painel_voluntario(request: Request, bemvindo: int = 0, criados: int = 0, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("voluntario"))):
        horarios = db.scalars(
            select(Horario)
            .options(selectinload(Horario.agendamentos).selectinload(Agendamento.estudante).selectinload(Usuario.escola))
            .where(Horario.voluntario_id == usuario.id)
            .order_by(Horario.inicio)
        ).all()
        agora = datetime.now()
        realizadas = monitorias_realizadas(horarios)
        return render(
            request,
            "voluntario.html",
            usuario,
            realizadas=len(realizadas),
            minutos_realizados=sum(h.duracao_min for h in realizadas),
            criados=max(0, criados),
            futuros=[h for h in horarios if h.inicio > agora],
            passados=[h for h in horarios if h.inicio <= agora][-20:],
            materias=MATERIAS,
            bemvindo=bemvindo,
            hoje=agora.strftime("%Y-%m-%d"),
            limite_presenca=agora + JANELA_PRESENCA,
        )

    @app.post("/voluntario/horarios", dependencies=[Depends(csrf_protect)])
    def criar_horario(
        data: str = Form(...),
        hora: str = Form(...),
        materia: str = Form(...),
        duracao_min: int = Form(60),
        modalidade: str = Form("online"),
        local_ou_link: str = Form(""),
        vagas: int = Form(1),
        dias: list[int] = Form([]),
        semanas: int = Form(1),
        db: Session = Depends(get_db),
        usuario: Usuario = Depends(exigir_papel("voluntario")),
    ):
        """Cria um horário único (sem dias marcados) ou uma grade semanal:
        os dias da semana marcados, a partir da data informada, por N semanas."""
        if not usuario.aprovado:
            raise HTTPException(403, "Seu cadastro ainda está em análise pela coordenação.")
        try:
            primeiro = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(400, "Data ou hora inválida.") from None
        if materia not in MATERIAS or modalidade not in ("online", "presencial"):
            raise HTTPException(400, "Matéria ou modalidade inválida.")
        if any(d not in range(7) for d in dias):
            raise HTTPException(400, "Dia da semana inválido.")
        agora = datetime.now()
        if dias:
            semanas = max(1, min(semanas, 8))
            inicios = [
                primeiro + timedelta(days=(d - primeiro.weekday()) % 7 + 7 * s)
                for s in range(semanas)
                for d in sorted(set(dias))
            ]
            inicios = [i for i in inicios if i > agora][:MAX_HORARIOS_POR_ENVIO]
            if not inicios:
                raise HTTPException(400, "Escolha uma data e hora no futuro.")
        else:
            if primeiro <= agora:
                raise HTTPException(400, "Escolha uma data e hora no futuro.")
            inicios = [primeiro]
        for inicio in inicios:
            db.add(
                Horario(
                    voluntario_id=usuario.id,
                    materia=materia,
                    inicio=inicio,
                    duracao_min=max(15, min(duracao_min, 180)),
                    modalidade=modalidade,
                    local_ou_link=local_ou_link.strip()[:300],
                    vagas=max(1, min(vagas, 10)),
                )
            )
        db.commit()
        return redirect(f"/voluntario?criados={len(inicios)}")

    @app.get("/voluntario/certificado", response_class=HTMLResponse)
    def certificado(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("voluntario"))):
        horarios = db.scalars(
            select(Horario)
            .options(selectinload(Horario.agendamentos))
            .where(Horario.voluntario_id == usuario.id, Horario.inicio <= datetime.now())
            .order_by(Horario.inicio)
        ).all()
        realizadas = monitorias_realizadas(horarios)
        return render(
            request,
            "certificado.html",
            usuario,
            realizadas=realizadas,
            minutos=sum(h.duracao_min for h in realizadas),
            emitido_em=datetime.now(),
        )

    @app.post("/agendamentos/{ag_id}/presenca", dependencies=[Depends(csrf_protect)])
    def presenca(ag_id: int, status: str = Form(...), db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("voluntario"))):
        ag = db.get(Agendamento, ag_id)
        if ag is None or ag.horario.voluntario_id != usuario.id:
            raise HTTPException(404, "Agendamento não encontrado.")
        if status not in ("realizado", "faltou") or ag.status == "cancelado":
            raise HTTPException(400, "Status inválido.")
        if ag.horario.inicio > datetime.now() + JANELA_PRESENCA:
            raise HTTPException(400, "A presença só pode ser registrada a partir de 1 hora antes do início da monitoria.")
        ag.status = status
        db.commit()
        return redirect("/voluntario")

    # ---------- Impacto (patrocinador / coordenação) ----------

    @app.get("/impacto", response_class=HTMLResponse)
    def impacto(request: Request, db: Session = Depends(get_db), usuario: Usuario | None = Depends(usuario_atual)):
        escolas = db.scalars(select(Escola).order_by(Escola.indice_prioridade.desc().nulls_last(), Escola.nome)).all()
        return render(request, "impacto.html", usuario, k=calcular_impacto(db), escolas=escolas)

    # ---------- Coordenação: aprovação de voluntários ----------

    @app.get("/coordenacao/voluntarios", response_class=HTMLResponse)
    def coord_voluntarios(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("coordenacao"))):
        pendentes = db.scalars(select(Usuario).where(Usuario.papel == "voluntario", Usuario.aprovado.is_(False)).order_by(Usuario.criado_em)).all()
        aprovados = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.papel == "voluntario", Usuario.aprovado.is_(True))) or 0
        return render(request, "coordenacao_voluntarios.html", usuario, pendentes=pendentes, aprovados=aprovados)

    @app.post("/coordenacao/voluntarios/{vid}", dependencies=[Depends(csrf_protect)])
    def coord_decidir(vid: int, decisao: str = Form(...), db: Session = Depends(get_db), usuario: Usuario = Depends(exigir_papel("coordenacao"))):
        v = db.get(Usuario, vid)
        if v is None or v.papel != "voluntario" or v.aprovado:
            raise HTTPException(404, "Cadastro não encontrado.")
        if decisao == "aprovar":
            v.aprovado = True
            auditar(db, "voluntario_aprovado", usuario)
        elif decisao == "recusar":
            apagar_usuario(db, v)
            auditar(db, "voluntario_recusado", usuario)
        else:
            raise HTTPException(400, "Decisão inválida.")
        db.commit()
        return redirect("/coordenacao/voluntarios")

    # ---------- API de integração ----------

    @app.post("/api/v1/manutencao/expurgo", dependencies=[Depends(exigir_api_key)])
    def api_expurgo():
        """Apaga agora os cadastros de menores sem autorização do responsável há mais de 30 dias
        (o app também faz isso sozinho na subida e a cada hora)."""
        return {"apagados": rodar_expurgo(app)}

    @app.post("/api/v1/assistente", dependencies=[Depends(csrf_header)])
    def api_assistente(dados: PerguntaAssistente, request: Request):
        """Assistente de IA Generativa (AI Bits): dúvidas sobre como usar a plataforma.

        Só o texto da pergunta vai ao modelo. Se o modelo falhar, devolve `fonte: "fallback"`.
        """
        assistente: Assistente = request.app.state.assistente
        try:
            assistente.registrar_uso(request.client.host if request.client else "desconhecido")
        except LimiteExcedido:
            raise HTTPException(429, "Muitas perguntas em pouco tempo. Espere um minuto e tente de novo.") from None
        return assistente.responder(dados.pergunta)

    @app.post("/api/v1/visao/endereco", dependencies=[Depends(csrf_header)])
    def api_visao_endereco(request: Request, arquivo: UploadFile = File(...)):
        """Visão Computacional: lê o endereço na foto (ou PDF) de uma conta de Enel, Sabesp ou Claro.

        Devolve os campos para o estudante **conferir** no cadastro; nada é gravado aqui.
        A imagem fica só em memória. `fonte`: `ocr`, `indisponivel` (OCR não instalado) ou `erro`.
        """
        leitor: LeitorEndereco = request.app.state.visao
        if (arquivo.content_type or "").lower() not in TIPOS_ACEITOS:
            raise HTTPException(415, "Envie uma foto (JPG, PNG ou WebP) ou o PDF da conta.")
        dados = arquivo.file.read(MAX_BYTES + 1)
        if len(dados) > MAX_BYTES:
            raise HTTPException(413, "Arquivo muito grande (máximo de 8 MB). Tire a foto de novo ou envie o PDF.")
        try:
            leitor.registrar_uso(request.client.host if request.client else "desconhecido")
        except LimiteVisao:
            raise HTTPException(429, "Muitas leituras em pouco tempo. Espere um minuto ou digite o bairro e o CEP.") from None
        try:
            return leitor.ler(dados)
        except ArquivoInvalido as e:
            raise HTTPException(422, str(e)) from e
        finally:
            del dados

    @app.get("/api/v1/impacto")
    def api_impacto(db: Session = Depends(get_db)):
        """Indicadores agregados e anônimos (sem dados pessoais)."""
        return calcular_impacto(db)

    @app.get("/api/v1/escolas")
    def api_escolas(db: Session = Depends(get_db)):
        return [
            {
                "id": e.id,
                "nome": e.nome,
                "bairro": e.bairro,
                "municipio": e.municipio,
                "codigo_inep": e.codigo_inep,
                "territorio_prioritario": e.territorio_prioritario,
                "indice_prioridade": e.indice_prioridade,
                "fonte_prioridade": e.fonte_prioridade,
            }
            for e in db.scalars(select(Escola).order_by(Escola.id)).all()
        ]

    @app.put("/api/v1/escolas/prioridade", dependencies=[Depends(exigir_api_key)])
    def api_prioridade(itens: list[PrioridadeEscola], db: Session = Depends(get_db)):
        """Contrato para o pipeline de Dados (Airflow) gravar a priorização territorial."""
        atualizadas = 0
        for item in itens:
            escola = None
            if item.escola_id is not None:
                escola = db.get(Escola, item.escola_id)
            elif item.codigo_inep:
                escola = db.scalar(select(Escola).where(Escola.codigo_inep == item.codigo_inep))
            if escola is None:
                continue
            escola.territorio_prioritario = item.territorio_prioritario
            escola.indice_prioridade = item.indice_prioridade
            escola.fonte_prioridade = "pipeline"
            atualizadas += 1
        db.commit()
        return {"atualizadas": atualizadas}

    @app.post("/api/v1/integracao/voluntarios", status_code=201, dependencies=[Depends(exigir_api_key)])
    def api_voluntarios_rpa(itens: list[object], db: Session = Depends(get_db)):
        """Contrato para o robô de RPA (UiPath) devolver os voluntários credenciados no SICREV.

        Cada voluntário entra como pendente de aprovação (`aprovado = False`) e a coordenação aprova
        em `/coordenacao/voluntarios`. Idempotente: apelido ou e-mail já existente volta em
        `rejeitados`, nada é duplicado. Um item inválido não derruba o lote.
        """
        if len(itens) > MAX_LOTE_RPA:
            raise HTTPException(413, f"Lote acima de {MAX_LOTE_RPA} voluntários. Divida o envio.")
        criados: list[str] = []
        rejeitados: list[str] = []
        motivos: dict[str, str] = {}
        vistos: set[str] = set()

        def rejeitar(rotulo: str, motivo: str) -> None:
            rejeitados.append(rotulo)
            motivos[rotulo] = motivo

        for i, bruto in enumerate(itens):
            rotulo = str(bruto.get("apelido", "")).strip()[:30] if isinstance(bruto, dict) else ""
            rotulo = rotulo or f"item_{i}"
            try:
                v = VoluntarioRPA.model_validate(bruto)
            except ValidationError as e:
                campos = sorted({str(err["loc"][0]) for err in e.errors() if err["loc"]})
                rejeitar(rotulo, "dados inválidos: " + ", ".join(campos) if campos else "dados inválidos")
                continue
            chave = v.apelido.lower()
            if chave in vistos or v.email in vistos:
                rejeitar(v.apelido, "repetido no lote")
                continue
            vistos.update({chave, v.email})
            if db.scalar(select(Usuario.id).where(func.lower(Usuario.apelido) == chave)):
                rejeitar(v.apelido, "apelido já cadastrado")
                continue
            if db.scalar(select(Usuario.id).where(Usuario.email == v.email)):
                rejeitar(v.apelido, "e-mail já cadastrado")
                continue
            db.add(
                Usuario(
                    apelido=v.apelido,
                    email=v.email,
                    bairro=v.bairro.strip() or None,
                    aceita_boletim=v.aceita_boletim,
                    papel="voluntario",
                    aprovado=False,
                    origem=ORIGEM_RPA,
                    # Sem senha utilizável: a conta só serve à coordenação até o voluntário definir a sua.
                    senha_hash="!rpa",
                )
            )
            criados.append(v.apelido)
        if criados:
            auditar(db, "voluntarios_rpa", None, quantidade=len(criados))
        db.commit()
        log.info("integracao RPA: enviados=%d criados=%d rejeitados=%d", len(itens), len(criados), len(rejeitados))
        return {"criados": criados, "rejeitados": rejeitados, "motivos": motivos}

    @app.get("/api/v1/agendamentos.csv", dependencies=[Depends(exigir_api_key)])
    def api_agendamentos_csv(db: Session = Depends(get_db)):
        """Export pseudonimizado para o robô de RPA (presenças → relatório de impacto)."""
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["agendamento_id", "estudante_pseudo", "escola", "territorio_prioritario", "materia", "inicio", "duracao_min", "status", "voluntario_pseudo"])
        ags = db.scalars(
            select(Agendamento).options(
                selectinload(Agendamento.horario), selectinload(Agendamento.estudante).selectinload(Usuario.escola)
            ).order_by(Agendamento.id)
        ).all()
        salt = app.state.settings.secret_key[:16]

        def pseudo(prefixo: str, uid: int) -> str:
            return prefixo + hashlib.sha256(f"{salt}{uid}".encode()).hexdigest()[:10]

        for a in ags:
            escola = a.estudante.escola
            w.writerow([
                a.id,
                pseudo("E-", a.estudante_id),
                escola.nome if escola else "",
                int(bool(escola and escola.territorio_prioritario)),
                a.horario.materia,
                a.horario.inicio.isoformat(timespec="minutes"),
                a.horario.duracao_min,
                a.status,
                pseudo("V-", a.horario.voluntario_id),
            ])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv; charset=utf-8")

    return app


app = create_app()
