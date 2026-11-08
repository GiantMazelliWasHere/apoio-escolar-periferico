"""Dados SINTÉTICOS de demonstração.

Escolas, pessoas e índices abaixo são fictícios: nenhum nome, e-mail ou número
corresponde a uma pessoa ou escola real. O índice de prioridade será substituído
pelo pipeline de Dados (INEP/IBGE) via PUT /api/v1/escolas/prioridade.

Não criamos histórico de monitorias passadas: o painel de impacto mostra apenas
o que acontecer de verdade na plataforma (evita números que pareçam resultados).

Contas de demonstração (senhas só para o ambiente de demo):
- estudante:   estudante.demo@exemplo.org   / estudante123
- voluntários: voluntario1..4@exemplo.org    / voluntario123
- coordenação: coordenacao.demo@exemplo.org / coordenacao123
"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Escola, Horario, Usuario
from .security import hash_senha

ESCOLAS = [
    ("EE Exemplo Jardim das Flores", "Jardim das Flores", True, 0.82),
    ("EE Exemplo Vila Esperança", "Vila Esperança", True, 0.77),
    ("EE Exemplo Parque do Sol", "Parque do Sol", True, 0.71),
    ("EE Exemplo Morro Azul", "Morro Azul", True, 0.68),
    ("EE Exemplo Centro Novo", "Centro Novo", False, 0.35),
    ("EE Exemplo Bela Vista", "Bela Vista", False, 0.29),
]

VOLUNTARIOS = [
    ("Carla (Licencianda em Matemática)", "voluntario1@exemplo.org", "Licenciatura em Matemática", ["Matemática", "Física"]),
    ("Rafael (Eng. de Software)", "voluntario2@exemplo.org", "Engenharia de Software", ["Programação", "Matemática"]),
    ("Beatriz (Letras)", "voluntario3@exemplo.org", "Letras Português/Inglês", ["Português", "Inglês"]),
    ("Diego (Biomedicina)", "voluntario4@exemplo.org", "Biomedicina", ["Biologia", "Química", "Ciências"]),
]

HORAS = [9, 14, 16, 18, 19]


def _criar_horarios_futuros(db: Session, agora: datetime) -> None:
    voluntarios = db.scalars(select(Usuario).where(Usuario.papel == "voluntario", Usuario.email.like("voluntario%@exemplo.org"))).all()
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
        for nome, bairro, prioritario, indice in ESCOLAS:
            db.add(Escola(nome=nome, bairro=bairro, municipio="Município Exemplo", territorio_prioritario=prioritario, indice_prioridade=indice, fonte_prioridade="sintetico"))
        db.flush()
        primeira = db.scalar(select(Escola).order_by(Escola.id))
        db.add(Usuario(nome="Estudante Demo", email="estudante.demo@exemplo.org", senha_hash=hash_senha("estudante123"), papel="estudante", escola_id=primeira.id, ano_escolar="9º ano EF", bairro=primeira.bairro, consentimento_responsavel=True, consentimento_em=agora))
        db.add(Usuario(nome="Coordenação Demo", email="coordenacao.demo@exemplo.org", senha_hash=hash_senha("coordenacao123"), papel="coordenacao"))
        for nome, email, formacao, _ in VOLUNTARIOS:
            db.add(Usuario(nome=nome, email=email, senha_hash=hash_senha("voluntario123"), papel="voluntario", formacao=formacao))
        db.flush()

    # Sempre garante horários futuros para a demo não "envelhecer".
    tem_futuro = db.scalar(select(Horario).where(Horario.inicio > agora + timedelta(days=2)).limit(1))
    if tem_futuro is None:
        _criar_horarios_futuros(db, agora)
    db.commit()
