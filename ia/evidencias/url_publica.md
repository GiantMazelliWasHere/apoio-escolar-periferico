# AI Bits na URL pública (Azure App Service)

Chamada feita em 18/11/2026 contra o MVP publicado, do mesmo jeito que a tela `/ajuda` faz: abre a página para pegar o cookie de sessão e o token CSRF e depois envia a pergunta.

```bash
U=https://app-apoioescolar-mvp-6e7462.azurewebsites.net
T=$(curl -s -c cj.txt "$U/ajuda" | grep -o 'name="csrf-token" content="[^"]*"' | sed 's/.*content="//;s/"$//')
curl -s -b cj.txt -H "Content-Type: application/json" -H "X-CSRF-Token: $T" \
  -d '{"pergunta":"Como eu marco uma monitoria?"}' "$U/api/v1/assistente"
```

Resposta (HTTP 200, 2,8 s):

```json
{
  "resposta": "Para marcar uma monitoria, você precisa estar com sua conta de estudante ativa. Se você já tem uma conta e ela foi autorizada pelo seu responsável (se você for menor de 18 anos), é bem fácil agendar!",
  "passos": [
    "Entre no site com seu apelido e senha.",
    "Toque no botão \"Monitorias\" no menu.",
    "Escolha a matéria que você precisa de ajuda (como Matemática ou Português) ou veja \"Todas\" as opções.",
    "Escolha o turno (manhã, tarde ou noite) e veja os horários disponíveis.",
    "Quando encontrar um horário que seja bom para você, toque em \"Agendar\", escreva sua dúvida e confirme."
  ],
  "categoria": "Agendamento",
  "acao": {"rotulo": "Ver monitorias", "url": "/monitorias"},
  "encaminhar_humano": false,
  "fonte": "ia"
}
```

`"fonte": "ia"` indica que a resposta veio do modelo. Sem chave ou com o modelo fora do ar, viria `"fonte": "fallback"`.
