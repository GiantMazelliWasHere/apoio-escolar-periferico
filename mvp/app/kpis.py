"""Indicadores de impacto calculados direto do banco.

As fórmulas seguem a seção 6 da entrega de Business
(docs/business/Entrega_Business_Apoio_Escolar_Periferico.md).

LGPD: contagens de pessoas entre 1 e 4 (K_MINIMO - 1) saem como None ("menos de 5"),
para ninguém ser identificado por um grupo pequeno. Só entram estudantes com o cadastro
autorizado pelo responsável (ou maiores de idade).
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .lgpd import K_MINIMO, suprimir
from .maker import ORIGEM_MAKER
from .models import CONSENTIMENTO_AUTORIZADO, CONSENTIMENTO_NAO_EXIGIDO, Agendamento, Escola, Horario, Usuario

ESTUDANTE_VALIDO = (Usuario.papel == "estudante", Usuario.consentimento_status.in_((CONSENTIMENTO_AUTORIZADO, CONSENTIMENTO_NAO_EXIGIDO)))


def calcular_impacto(db: Session, agora: datetime | None = None) -> dict:
    agora = agora or datetime.now()
    inicio_janela = agora - timedelta(days=30)

    estudantes = db.scalar(select(func.count()).select_from(Usuario).where(*ESTUDANTE_VALIDO)) or 0
    estudantes_prioritarios = (
        db.scalar(
            select(func.count())
            .select_from(Usuario)
            .join(Escola, Usuario.escola_id == Escola.id)
            .where(*ESTUDANTE_VALIDO, Escola.territorio_prioritario.is_(True))
        )
        or 0
    )

    ativos = (
        db.scalar(
            select(func.count(func.distinct(Agendamento.estudante_id))).where(
                Agendamento.status != "cancelado", Agendamento.criado_em >= inicio_janela
            )
        )
        or 0
    )

    cadastros_maker = (
        db.scalar(select(func.count()).select_from(Usuario).where(Usuario.origem == ORIGEM_MAKER, Usuario.papel != "estudante"))
        or 0
    ) + (
        db.scalar(select(func.count()).select_from(Usuario).where(Usuario.origem == ORIGEM_MAKER, *ESTUDANTE_VALIDO)) or 0
    )

    def contar(status: str) -> int:
        return db.scalar(select(func.count()).select_from(Agendamento).where(Agendamento.status == status)) or 0

    agendadas = contar("agendado")
    realizadas = contar("realizado")
    faltas = contar("faltou")

    minutos = (
        db.scalar(
            select(func.coalesce(func.sum(Horario.duracao_min), 0))
            .select_from(Agendamento)
            .join(Horario, Agendamento.horario_id == Horario.id)
            .where(Agendamento.status == "realizado")
        )
        or 0
    )

    voluntarios = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.papel == "voluntario")) or 0
    voluntarios_ativos = (
        db.scalar(
            select(func.count(func.distinct(Horario.voluntario_id))).where(
                Horario.inicio >= inicio_janela, Horario.inicio <= agora + timedelta(days=30)
            )
        )
        or 0
    )
    horarios_futuros = db.scalar(select(func.count()).select_from(Horario).where(Horario.inicio > agora)) or 0

    por_materia = dict(
        db.execute(
            select(Horario.materia, func.count())
            .select_from(Agendamento)
            .join(Horario, Agendamento.horario_id == Horario.id)
            .where(Agendamento.status != "cancelado")
            .group_by(Horario.materia)
            .order_by(func.count().desc())
        ).all()
    )

    def pct(a: int, b: int) -> float | None:
        return round(100 * a / b, 1) if b else None

    def pct_protegido(parte: int, total: int) -> float | None:
        # Um percentual também revela grupos pequenos: as duas partes precisam ter 0 ou >= K_MINIMO.
        if suprimir(parte) is None or suprimir(total - parte) is None:
            return None
        return pct(parte, total)

    materias_visiveis = {m: n for m, n in por_materia.items() if n >= K_MINIMO}

    return {
        "estudantes_cadastrados": suprimir(estudantes),
        "estudantes_ativos_30d": suprimir(ativos),
        "pct_estudantes_territorio_prioritario": pct_protegido(estudantes_prioritarios, estudantes),
        "monitorias_agendadas": agendadas,
        "monitorias_realizadas": realizadas,
        "faltas": suprimir(faltas),
        "taxa_presenca": pct(realizadas, realizadas + faltas) if realizadas + faltas >= K_MINIMO else None,
        "horas_reforco": round(minutos / 60, 1),
        "voluntarios_cadastrados": voluntarios,
        "voluntarios_ativos_30d": voluntarios_ativos,
        "oportunidades_abertas": horarios_futuros,
        "cadastros_via_peca_maker": suprimir(cadastros_maker),
        "agendamentos_por_materia": materias_visiveis,
        "materias_ocultas": len(por_materia) - len(materias_visiveis),
        "k_minimo": K_MINIMO,
        "calculado_em": agora.isoformat(timespec="seconds"),
    }
