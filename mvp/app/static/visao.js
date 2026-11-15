// Cadastro: lê bairro e CEP da foto de uma conta (Visão Computacional).
// A foto vai só para /api/v1/visao/endereco e não é guardada. Todo texto entra por textContent.
(function () {
  var caixa = document.getElementById("visao");
  if (!caixa || caixa.dataset.ativa !== "1" || !window.fetch || !window.FormData) return;

  var arquivo = document.getElementById("visao-arquivo");
  var status = document.getElementById("visao-status");
  var resultado = document.getElementById("visao-resultado");
  var empresa = document.getElementById("visao-empresa");
  var endereco = document.getElementById("visao-endereco");
  var bairro = document.getElementById("bairro");
  var cep = document.getElementById("cep");
  var csrf = document.querySelector('meta[name="csrf-token"]').content;
  var MAX = 8 * 1024 * 1024;
  caixa.hidden = false;

  function preencher(campo, valor) {
    if (!valor) return false;
    campo.value = valor;
    campo.classList.add("campo-lido");
    return true;
  }

  [bairro, cep].forEach(function (c) {
    c.addEventListener("input", function () { c.classList.remove("campo-lido"); });
  });

  arquivo.addEventListener("change", function () {
    var f = arquivo.files && arquivo.files[0];
    if (!f) return;
    resultado.hidden = true;
    if (f.size > MAX) {
      status.textContent = "Arquivo muito grande (máximo de 8 MB). Tire a foto de novo ou digite o bairro e o CEP.";
      arquivo.value = "";
      return;
    }
    status.textContent = "Lendo a conta… pode levar alguns segundos.";
    arquivo.disabled = true;
    var dados = new FormData();
    dados.append("arquivo", f);
    fetch("/api/v1/visao/endereco", { method: "POST", headers: { "X-CSRF-Token": csrf }, body: dados })
      .then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, d: d }; }, function () { return { ok: false, d: {} }; });
      })
      .then(function (res) {
        var d = res.d;
        if (!res.ok) {
          status.textContent = typeof d.detail === "string" ? d.detail : "Não consegui ler o arquivo. Digite o bairro e o CEP.";
          return;
        }
        if (d.fonte !== "ocr") {
          status.textContent = "A leitura automática não está disponível agora. Digite o bairro e o CEP.";
          return;
        }
        var achouBairro = preencher(bairro, d.bairro);
        var achouCep = preencher(cep, d.cep);
        if (!achouBairro && !achouCep) {
          status.textContent = "Não encontramos o endereço nesta foto. Tente uma foto mais de perto, de frente e com boa luz, ou digite o bairro e o CEP.";
          return;
        }
        var partes = [];
        if (d.logradouro) partes.push(d.logradouro + (d.numero ? ", " + d.numero : ""));
        if (d.bairro) partes.push(d.bairro);
        if (d.cep) partes.push("CEP " + d.cep);
        endereco.textContent = partes.join(" · ");
        empresa.textContent = d.empresa_nome || "Conta";
        resultado.hidden = false;
        status.textContent = achouBairro && achouCep
          ? "Pronto! Confira o bairro e o CEP."
          : "Lemos só parte do endereço. Complete o que faltar.";
        (achouBairro ? bairro : cep).focus();
      })
      .catch(function () {
        status.textContent = "Sem conexão agora. Digite o bairro e o CEP ou tente de novo.";
      })
      .then(function () {
        arquivo.disabled = false;
        arquivo.value = "";
      });
  });
})();
