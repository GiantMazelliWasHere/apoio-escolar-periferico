// Botão "Copiar link" da tela de autorização do responsável.
(() => {
  const botao = document.getElementById("copiar-link");
  const status = document.getElementById("copiar-status");
  if (!botao) return;
  botao.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(botao.dataset.link);
      status.textContent = "Link copiado. Cole na conversa com o seu responsável.";
    } catch {
      status.textContent = "Não deu para copiar sozinho: toque e segure no link acima para copiar.";
    }
  });
})();
