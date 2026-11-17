"""Telemetria no Azure Application Insights (OpenTelemetry).

Só liga quando a variável APPLICATIONINSIGHTS_CONNECTION_STRING existe (o App Service recebe
a connection string pelo script infra/provisionar.sh). Localmente e no CI nada é enviado.

Privacidade (LGPD): os logs da aplicação não levam nome, e-mail nem conteúdo de formulário;
a telemetria registra rota, status e duração das requisições.
"""
import logging
import os

log = logging.getLogger("apoio")


def configurar_telemetria(app) -> bool:
    conexao = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()
    if not conexao:
        return False
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:  # pacote ausente: a aplicação segue sem telemetria
        log.warning("azure-monitor-opentelemetry não instalado; telemetria desligada.")
        return False
    os.environ.setdefault("OTEL_SERVICE_NAME", "apoio-escolar-mvp")
    configure_azure_monitor(connection_string=conexao)  # logs do logger raiz (INFO+) vão como traces
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("azure").setLevel(logging.WARNING)  # o próprio SDK é verboso
    # /health é sondado a cada minuto pelo App Service: fica fora para não poluir as métricas.
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health")
    log.info("Telemetria do Application Insights ligada.")
    return True
