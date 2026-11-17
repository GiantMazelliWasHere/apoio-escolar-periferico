"""Dados SINTÉTICOS de demonstração.

Escolas, pessoas e índices abaixo são fictícios: nenhum nome, e-mail ou número
corresponde a uma pessoa ou escola real. Os códigos INEP começam com 99 (UF
inexistente) para nunca coincidirem com uma escola real; são os mesmos que o
pipeline de Dados (dados/dags) usa para enviar a prioridade territorial via
PUT /api/v1/escolas/prioridade.

Não criamos histórico de monitorias passadas: o painel de impacto mostra apenas
o que acontecer de verdade na plataforma (evita números que pareçam resultados).

Contas de demonstração (senhas só para o ambiente de demo):
- estudante:   apelido estudante.demo        / estudante123 (autorizado pelo responsável)
- voluntários: voluntario1..4@exemplo.org    / voluntario123 (aprovados)
               voluntario5@exemplo.org       / voluntario123 (em análise: a coordenação aprova)
- coordenação: coordenacao.demo@exemplo.org / coordenacao123
"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .lgpd import AVISO_VERSAO
from .models import CONSENTIMENTO_AUTORIZADO, Escola, Horario, Usuario
from .security import hash_senha

ESCOLAS = [
    ("EE Exemplo Jardim das Flores", "Jardim das Flores", True, 0.82, "99000101"),
    ("EE Exemplo Vila Esperança", "Vila Esperança", True, 0.77, "99000102"),
    ("EE Exemplo Parque do Sol", "Parque do Sol", True, 0.71, "99000103"),
    ("EE Exemplo Morro Azul", "Morro Azul", True, 0.68, "99000104"),
    ("EE Exemplo Centro Novo", "Centro Novo", False, 0.35, "99000105"),
    ("EE Exemplo Bela Vista", "Bela Vista", False, 0.29, "99000106"),
]

VOLUNTARIOS = [
    ("Carla (Licencianda em Matemática)", "voluntario1@exemplo.org", "Licenciatura em Matemática", ["Matemática", "Física"]),
    ("Rafael (Eng. de Software)", "voluntario2@exemplo.org", "Engenharia de Software", ["Programação", "Matemática"]),
    ("Beatriz (Letras)", "voluntario3@exemplo.org", "Letras Português/Inglês", ["Português", "Inglês"]),
    ("Diego (Biomedicina)", "voluntario4@exemplo.org", "Biomedicina", ["Biologia", "Química", "Ciências"]),
]
VOLUNTARIO_EM_ANALISE = ("Elisa (Pedagogia)", "voluntario5@exemplo.org", "Pedagogia")

HORAS = [9, 14, 16, 18, 19]


def _criar_horarios_futuros(db: Session, agora: datetime) -> None:
    voluntarios = db.scalars(select(Usuario).where(Usuario.papel == "voluntario", Usuario.aprovado.is_(True), Usuario.email.like("voluntario%@exemplo.org"))).all()
    materias_por_email = {email: mats for _, email, _, mats in VOLUNTARIOS}
    base = agora.replace(minute=0, second=0, microsecond=0)
    for i, vol in enumerate(voluntarios):
        mats = materias_por_email.get(vol.email, ["Matemática"])
        for dia in range(1, 15):
            if (dia + i) % 2:  # dias alternados para cada voluntário
                continue
            hora = HORAS[(dia + i) % len(HORAS)]
            inicio = (base + timedelta(days=dia)).replace(hour=hora)
            db.add(
                Horario(
                    voluntario_id=vol.id,
                    materia=mats[dia % len(mats)],
                    inicio=inicio,
                    duracao_min=60,
                    modalidade="online",
                    local_ou_link="Link enviado pelo monitor no dia",
                    vagas=3,
                )
            )


def seed_demo(db: Session) -> None:
    agora = datetime.now()
    if db.scalar(select(Escola).limit(1)) is None:
        for nome, bairro, prioritario, indice, inep in ESCOLAS:
            db.add(Escola(nome=nome, bairro=bairro, municipio="Município Exemplo", territorio_prioritario=prioritario, indice_prioridade=indice, fonte_prioridade="sintetico", codigo_inep=inep))
        db.flush()
        db.add(Usuario(nome="Coordenação Demo", email="coordenacao.demo@exemplo.org", senha_hash=hash_senha("coordenacao123"), papel="coordenacao"))
        for nome, email, formacao, _ in VOLUNTARIOS:
            db.add(Usuario(nome=nome, email=email, senha_hash=hash_senha("voluntario123"), papel="voluntario", formacao=formacao, aprovado=True))
        db.flush()

    # Contas de demonstração do fluxo LGPD (também em bancos criados antes dele).
    if db.scalar(select(Usuario).where(Usuario.apelido == "estudante.demo")) is None:
        primeira = db.scalar(select(Escola).order_by(Escola.id))
        db.add(Usuario(
            apelido="estudante.demo", senha_hash=hash_senha("estudante123"), papel="estudante", faixa_idade="13 a 15 anos",
            escola_id=primeira.id, ano_escolar="9º ano EF", bairro=primeira.bairro,
            consentimento_status=CONSENTIMENTO_AUTORIZADO, consentimento_responsavel=True, consentimento_em=agora,
            aviso_versao=AVISO_VERSAO, aviso_aceito_em=agora,
        ))
    nome, email, formacao = VOLUNTARIO_EM_ANALISE
    if db.scalar(select(Usuario).where(Usuario.email == email)) is None:
        db.add(Usuario(nome=nome, email=email, senha_hash=hash_senha("voluntario123"), papel="voluntario", formacao=formacao, aprovado=False))
    db.flush()

    # Bancos criados antes da integração com o pipeline de Dados não têm o código INEP.
    codigos = {nome: inep for nome, _, _, _, inep in ESCOLAS}
    for escola in db.scalars(select(Escola).where(Escola.codigo_inep.is_(None))).all():
        escola.codigo_inep = codigos.get(escola.nome)

    # Sempre garante horários futuros para a demo não "envelhecer".
    tem_futuro = db.scalar(select(Horario).where(Horario.inicio > agora + timedelta(days=2)).limit(1))
    if tem_futuro is None:
        _criar_horarios_futuros(db, agora)
    db.commit()
