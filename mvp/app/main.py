"""Núcleo do MVP — Apoio Escolar Periférico.

Fluxo central: cadastro do estudante → busca de monitoria por matéria →
agendamento → voluntário registra presença → painel de impacto.
"""
import csv
import hashlib
import io
import re
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.middleware.sessions import SessionMiddleware

from .assistente import FAQ, MAX_PERGUNTA, NOME_ASSISTENTE, Assistente, LimiteExcedido, criar_chamada_openrouter
from .config import Settings
from .db import Base, adicionar_colunas_novas, get_db, make_sessionmaker
from .kpis import calcular_impacto
from .models import ANOS_ESCOLARES, MATERIAS, TURNOS, Agendamento, Escola, Horario, Usuario
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
from .visao import MAX_BYTES, TIPOS_ACEITOS, ArquivoInvalido, LeitorEndereco, criar_ocr_easyocr
from .visao import LimiteExcedido as LimiteVisao

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

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


class PerguntaAssistente(BaseModel):
    pergunta: str = Field(max_length=MAX_PERGUNTA)

    @field_validator("pergunta")
    @classmethod
    def _nao_vazia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Escreva a sua dúvida.")
        return v


def normalizar_cep(cep: str) -> str | None:
    """"01234567", "01234-567" ou "01.234-567" → "01234-567". Vazio → None. Inválido → ValueError."""
    digitos = re.sub(r"\D", "", cep or "")
    if not digitos:
        return None
    if len(digitos) != 8:
        raise ValueError(cep)
    return f"{digitos[:5]}-{digitos[5:]}"


def create_app(database_url: str | None = None, seed: bool | None = None) -> FastAPI:
    settings = Settings()
    app = FastAPI(title="Apoio Escolar Periférico — MVP", docs_url="/api/docs", redoc_url=None)
    app.state.settings = settings
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

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="aep_sessao",
        same_site="lax",
        https_only=settings.https_only_cookies,
        max_age=60 * 60 * 8,
    )
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    def render(request: Request, nome: str, usuario: Usuario | None, status_code: int = 200, **ctx) -> HTMLResponse:
        ctx.update(usuario=usuario, csrf_token=csrf_token(request), demo=True)
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
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def inicio(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "index.html", usuario, materias=MATERIAS)

    @app.get("/privacidade", response_class=HTMLResponse)
    def privacidade(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "privacidade.html", usuario)

    @app.get("/ajuda", response_class=HTMLResponse)
    def ajuda(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "ajuda.html", usuario, faq=FAQ, assistente=NOME_ASSISTENTE, ia_ativa=request.app.state.assistente.ativo, max_pergunta=MAX_PERGUNTA)

    # ---------- Autenticação ----------

    @app.get("/entrar", response_class=HTMLResponse)
    def entrar_form(request: Request, proximo: str = "", usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "entrar.html", usuario, proximo=proximo)

    @app.post("/entrar", dependencies=[Depends(csrf_protect)])
    def entrar(request: Request, email: str = Form(...), senha: str = Form(...), proximo: str = Form(""), db: Session = Depends(get_db)):
        u = db.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))
        if u is None or not verificar_senha(senha, u.senha_hash):
            return render(request, "entrar.html", None, status_code=400, erro="E-mail ou senha incorretos.", proximo=proximo)
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
        return render(request, "cadastro_estudante.html", usuario, escolas=escolas, anos=ANOS_ESCOLARES, form={}, visao_ativa=request.app.state.visao.ativo)

    @app.post("/cadastro/estudante", dependencies=[Depends(csrf_protect)])
    def cadastro_estudante(
        request: Request,
        nome: str = Form(...),
        email: str = Form(...),
        senha: str = Form(...),
        escola_id: int = Form(...),
        ano_escolar: str = Form(...),
        bairro: str = Form(""),
        cep: str = Form(""),
        consentimento: str | None = Form(None),
        db: Session = Depends(get_db),
    ):
        email = email.strip().lower()
        form = {"nome": nome, "email": email, "escola_id": escola_id, "ano_escolar": ano_escolar, "bairro": bairro, "cep": cep}
        erro = None
        try:
            cep_ok = normalizar_cep(cep)
        except ValueError:
            cep_ok = None
        if not consentimento:
            erro = "Para menores de 18 anos, precisamos do consentimento do responsável. Marque a caixa de consentimento."
        elif len(senha) < 8:
            erro = "A senha precisa ter pelo menos 8 caracteres."
        elif db.scalar(select(Usuario).where(Usuario.email == email)):
            erro = "Este e-mail já tem cadastro. Use \"Entrar\"."
        elif db.get(Escola, escola_id) is None or ano_escolar not in ANOS_ESCOLARES:
            erro = "Escolha a escola e o ano escolar da lista."
        elif cep.strip() and cep_ok is None:
            erro = "O CEP precisa ter 8 números (ex.: 08250-000). Se não souber, deixe em branco."
        if erro:
            escolas = db.scalars(select(Escola).order_by(Escola.nome)).all()
            return render(request, "cadastro_estudante.html", None, status_code=400, erro=erro, escolas=escolas, anos=ANOS_ESCOLARES, form=form, visao_ativa=request.app.state.visao.ativo)
        u = Usuario(
            nome=nome.strip(),
            email=email,
            senha_hash=hash_senha(senha),
            papel="estudante",
            escola_id=escola_id,
            ano_escolar=ano_escolar,
            bairro=bairro.strip()[:120] or None,
            cep=cep_ok,
            consentimento_responsavel=True,
            consentimento_em=datetime.now(),
        )
        db.add(u)
        db.commit()
        entrar_na_sessao(request, u)
        return redirect("/monitorias?bemvindo=1")

    @app.get("/cadastro/voluntario", response_class=HTMLResponse)
    def cadastro_voluntario_form(request: Request, usuario: Usuario | None = Depends(usuario_atual)):
        return render(request, "cadastro_voluntario.html", usuario, form={})

    @app.post("/cadastro/voluntario", dependencies=[Depends(csrf_protect)])
    def cadastro_voluntario(
        request: Request,
        nome: str = Form(...),
        email: str = Form(...),
        senha: str = Form(...),
        formacao: str = Form(""),
        db: Session = Depends(get_db),
    ):
        email = email.strip().lower()
        erro = None
        if len(senha) < 8:
            erro = "A senha precisa ter pelo menos 8 caracteres."
        elif db.scalar(select(Usuario).where(Usuario.email == email)):
            erro = "Este e-mail já tem cadastro. Use \"Entrar\"."
        if erro:
            return render(request, "cadastro_voluntario.html", None, status_code=400, erro=erro, form={"nome": nome, "email": email, "formacao": formacao})
        u = Usuario(nome=nome.strip(), email=email, senha_hash=hash_senha(senha), papel="voluntario", formacao=formacao.strip() or None)
        db.add(u)
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
        try:
            primeiro = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(400, "Data ou hora inválida.")
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

    # ---------- API de integração ----------

    @app.post("/api/v1/assistente", dependencies=[Depends(csrf_header)])
    def api_assistente(dados: PerguntaAssistente, request: Request):
        """Assistente de IA Generativa (AI Bits): dúvidas sobre como usar a plataforma.

        Só o texto da pergunta vai ao modelo. Se o modelo falhar, devolve `fonte: "fallback"`.
        """
        assistente: Assistente = request.app.state.assistente
        try:
            assistente.registrar_uso(request.client.host if request.client else "desconhecido")
        except LimiteExcedido:
            raise HTTPException(429, "Muitas perguntas em pouco tempo. Espere um minuto e tente de novo.")
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
            raise HTTPException(429, "Muitas leituras em pouco tempo. Espere um minuto ou digite o bairro e o CEP.")
        try:
            return leitor.ler(dados)
        except ArquivoInvalido as e:
            raise HTTPException(422, str(e))
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
