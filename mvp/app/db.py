from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


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


def adicionar_colunas_novas(engine) -> None:
    """Migração mínima: `create_all` não altera tabelas existentes, então colunas
    opcionais criadas depois da 1ª versão são adicionadas aqui (bancos já no ar)."""
    novas = {"usuarios": {"cep": "VARCHAR(9)", "origem": "VARCHAR(30)"}}
    insp = inspect(engine)
    with engine.begin() as conn:
        for tabela, colunas in novas.items():
            if not insp.has_table(tabela):
                continue
            existentes = {c["name"] for c in insp.get_columns(tabela)}
            for nome, tipo in colunas.items():
                if nome not in existentes:
                    conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}"))


def get_db(request: Request):
    db: Session = request.app.state.SessionLocal()
    try:
        yield db
    finally:
        db.close()
