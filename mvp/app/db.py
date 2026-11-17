from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.schema import CreateTable


class Base(DeclarativeBase):
    pass


def make_sessionmaker(url: str) -> sessionmaker:
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        caminho = url.split("sqlite:///", 1)[-1]
        if caminho and caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **kwargs)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Colunas opcionais criadas depois da 1ª versão: `create_all` não altera tabelas existentes.
COLUNAS_NOVAS = {
    "usuarios": {
        "cep": "VARCHAR(9)",
        "origem": "VARCHAR(30)",
        "aviso_versao": "VARCHAR(20)",
        "aviso_aceito_em": "DATETIME",
        "apelido": "VARCHAR(30)",
        "faixa_idade": "VARCHAR(20)",
        "consentimento_status": "VARCHAR(20)",
        "consentimento_token_hash": "VARCHAR(64)",
        "consentimento_expira_em": "DATETIME",
        "email_responsavel_cifrado": "TEXT",
        "aprovado": "BOOLEAN DEFAULT 1",
        "aceita_boletim": "BOOLEAN",  # voluntários antigos continuam aprovados
    }
}


def adicionar_colunas_novas(engine) -> None:
    """Migração mínima para bancos já no ar: acrescenta colunas novas e, no SQLite, refaz a
    tabela `usuarios` da 1ª versão (nome e e-mail eram obrigatórios; hoje o estudante não tem)."""
    insp = inspect(engine)
    with engine.begin() as conn:
        for tabela, colunas in COLUNAS_NOVAS.items():
            if not insp.has_table(tabela):
                continue
            existentes = {c["name"] for c in insp.get_columns(tabela)}
            for nome, tipo in colunas.items():
                if nome not in existentes:
                    conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}"))  # noqa: S608 (nomes fixos acima)
    if engine.dialect.name == "sqlite":
        _refazer_usuarios_sqlite(engine)


def _refazer_usuarios_sqlite(engine) -> None:
    from .models import Usuario  # import tardio: models importa Base daqui

    insp = inspect(engine)
    if not insp.has_table("usuarios"):
        return
    tabela = Usuario.__table__
    antigas = {c["name"] for c in insp.get_columns("usuarios")}
    obrigatorias = {c["name"] for c in insp.get_columns("usuarios") if not c["nullable"]}
    faltando = {c.name for c in tabela.columns} - antigas
    if not (obrigatorias & {"nome", "email"} or faltando):
        return
    colunas = ", ".join(c.name for c in tabela.columns if c.name in antigas)
    ddl = str(CreateTable(tabela).compile(engine)).replace("CREATE TABLE usuarios", "CREATE TABLE usuarios_nova", 1)
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        conn.exec_driver_sql(ddl)
        # Nomes de coluna vêm do modelo SQLAlchemy, nunca de entrada do usuário.
        conn.exec_driver_sql(f"INSERT INTO usuarios_nova ({colunas}) SELECT {colunas} FROM usuarios")  # noqa: S608  # nosec B608
        conn.exec_driver_sql("DROP TABLE usuarios")
        conn.exec_driver_sql("ALTER TABLE usuarios_nova RENAME TO usuarios")
        for indice in tabela.indexes:
            indice.create(conn)
        # Estudantes da 1ª versão: viram apelido "estudante<id>", sem nome nem e-mail (minimização).
        conn.exec_driver_sql(
            "UPDATE usuarios SET apelido = 'estudante' || id, nome = NULL, email = NULL, "
            "consentimento_status = CASE WHEN consentimento_responsavel THEN 'autorizado' ELSE 'pendente' END "
            "WHERE papel = 'estudante' AND apelido IS NULL"
        )
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")


def get_db(request: Request):
    db: Session = request.app.state.SessionLocal()
    try:
        yield db
    finally:
        db.close()
