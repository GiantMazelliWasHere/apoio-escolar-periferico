"""Configuração do webserver do Airflow só para uso LOCAL (docker-compose.yml).

Visitante anônimo entra como Admin, para abrir a interface sem senha e tirar
as evidências. Nunca use isso num Airflow exposto na internet.
"""
from airflow.providers.fab.auth_manager.security_manager.override import FabAirflowSecurityManagerOverride  # noqa: F401
from flask_appbuilder.const import AUTH_DB

AUTH_TYPE = AUTH_DB
AUTH_ROLE_PUBLIC = "Admin"
WTF_CSRF_ENABLED = True
