from typing import List, Optional
from pydantic import BaseModel, Field

class EduConectaHelperOutput(BaseModel):
    """Esquema de saída estruturada para o EduConecta Helper Bot."""
    protocolo_atendimento: str = Field(
        description="Identificador único da interação de suporte"
    )
    intencao_detectada: str = Field(
        description="Intenção classificada (ex: Como_Funciona, Erro_Upload_Comprovante, Agendar_Monitoria, Dificuldade_Pedagogica)"
    )
    categoria_duvida: str = Field(
        description="Plataforma, Visao_Computacional, Reforco_Escolar ou Geral"
    )
    resposta_humanizada: str = Field(
        description="Resposta acolhedora, empática, clara e sem jargões técnicos para o estudante"
    )
    passos_para_solucao: List[str] = Field(
        description="Lista ordenada de ações que o usuário deve executar para solucionar a dúvida"
    )
    acao_sugerida_ui: str = Field(
        description="Comando para a interface (ex: ABRIR_MODAL_CAMERA, NAVEGAR_PARA_AULAS, NENHUMA)"
    )
    concessionaria_mencionada: Optional[str] = Field(
        default=None,
        description="ENEL, SABESP, CLARO ou OUTRA, se identificada na mensagem"
    )
    precisa_suporte_humano: bool = Field(
        default=False,
        description="True se a IA identificar necessidade de atendimento por monitor voluntário humano"
    )
