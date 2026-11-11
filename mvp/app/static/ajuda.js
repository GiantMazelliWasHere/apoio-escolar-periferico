// Chat da tela "Ajuda". Todo texto entra por textContent (nunca innerHTML).
(function () {
  var chat = document.getElementById("chat");
  var form = document.getElementById("chat-form");
  if (!chat || !form || chat.dataset.ia !== "1") return;

  var log = document.getElementById("chat-mensagens");
  var campo = document.getElementById("pergunta");
  var botao = document.getElementById("chat-enviar");
  var csrf = document.querySelector('meta[name="csrf-token"]').content;
  form.hidden = false;

  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto) e.textContent = texto;
    return e;
  }

  function balao(quem, texto) {
    var b = el("div", "balao balao-" + quem);
    b.appendChild(el("p", "sr", quem === "voce" ? "Você:" : "Assistente:"));
    b.appendChild(el("p", "", texto));
    log.appendChild(b);
    b.scrollIntoView({ block: "nearest" });
    return b;
  }

  function mostrarResposta(d) {
    var b = balao("ia", d.resposta);
    if (d.passos && d.passos.length) {
      var ol = el("ol", "passos");
      d.passos.forEach(function (p) { ol.appendChild(el("li", "", p)); });
      b.appendChild(ol);
    }
    if (d.encaminhar_humano && d.fonte === "ia") {
      b.appendChild(el("p", "ajuda", "Um monitor de verdade pode ajudar melhor com isso."));
    }
    // Só caminhos internos viram link (a lista de ações também é fixa no servidor).
    if (d.acao && typeof d.acao.url === "string" && /^\/[a-z]/.test(d.acao.url)) {
      var a = el("a", "botao botao-sec botao-pq", d.acao.rotulo);
      a.href = d.acao.url;
      b.appendChild(a);
    }
    b.scrollIntoView({ block: "nearest" });
  }

  function perguntar(texto) {
    texto = texto.trim();
    if (!texto || botao.disabled) return;
    balao("voce", texto);
    campo.value = "";
    botao.disabled = true;
    var espera = balao("ia", "Pensando…");
    fetch("/api/v1/assistente", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: JSON.stringify({ pergunta: texto }),
    })
      .then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, status: r.status, d: d }; });
      })
      .then(function (res) {
        espera.remove();
        if (res.ok) return mostrarResposta(res.d);
        var msg = res.status === 429 || res.status === 403 ? res.d.detail : null;
        balao("ia", typeof msg === "string" ? msg : "Não consegui entender a pergunta. Tente escrever de outro jeito.");
      })
      .catch(function () {
        espera.remove();
        balao("ia", "Sem conexão agora. Veja as perguntas frequentes abaixo ou tente de novo em instantes.");
      })
      .then(function () {
        botao.disabled = false;
        campo.focus();
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    perguntar(campo.value);
  });
  form.querySelectorAll("[data-pergunta]").forEach(function (b) {
    b.addEventListener("click", function () { perguntar(b.dataset.pergunta); });
  });
})();
