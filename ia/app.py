import os
import json
import mimetypes
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from client import tirar_duvida_helper

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Bits — EduConecta Periferia</title>
  
  <!-- Favicons Oficiais -->
  <link rel="icon" type="image/png" sizes="32x32" href="/img/icon/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/img/icon/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/img/icon/apple-touch-icon.png">
  <link rel="shortcut icon" href="/img/icon/favicon.ico">
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              lime: '#C7FB03',
              green: '#10B981',
              darkgreen: '#064E3B',
              dark: '#0B0F19'
            }
          }
        }
      }
    }
  </script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    .msg-anim { animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
    
    /* Scrollbar sutil */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(100, 116, 139, 0.3); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(100, 116, 139, 0.5); }
  </style>
</head>
<body class="min-h-screen flex flex-col font-sans transition-colors duration-200 bg-slate-950 text-slate-100" id="body-root">

  <!-- Header -->
  <header id="main-header" class="border-b transition-colors duration-200 sticky top-0 z-50 px-4 py-3 bg-slate-900 border-emerald-900/50 shadow-md">
    <div class="max-w-4xl mx-auto flex items-center justify-between">
      
      <!-- Brand & Team Info (Esquerda) -->
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-slate-900 p-1 border border-emerald-500/50 shadow-md flex items-center justify-center overflow-hidden flex-shrink-0">
          <img src="/img/logo%20IA%20bits.png" alt="AI Bits Logo" class="w-full h-full object-contain">
        </div>
        <div>
          <h1 class="font-bold text-lg leading-tight text-white" id="header-title">
            AI Bits
          </h1>
          <p class="text-xs text-slate-400" id="header-team">Suporte EduConecta Periferia</p>
        </div>
      </div>

      <!-- Controls: EduConecta à Direita & Theme Toggle (Sem o Online) -->
      <div class="flex items-center gap-2.5">
        <!-- Badge EduConecta posicionado à Direita -->
        <span id="educonecta-badge" class="text-xs font-semibold px-3 py-1 rounded-full border transition-colors shadow-sm bg-emerald-950/80 text-emerald-300 border-emerald-700/50 tracking-wide">
          EduConecta
        </span>

        <!-- Theme Toggle Button -->
        <button 
          id="theme-toggle-btn"
          onclick="toggleTheme()" 
          title="Alternar entre Modo Claro e Modo Escuro"
          class="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-xl border transition shadow-sm bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200">
          <i id="theme-icon" class="fa-solid fa-moon text-cyan-300"></i>
          <span id="theme-text" class="hidden sm:inline">Modo Escuro</span>
        </button>
      </div>

    </div>
  </header>

  <!-- Chat Container -->
  <main class="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col">
    <!-- Messages Scroll Area -->
    <div id="chat-messages" class="flex-1 space-y-4 overflow-y-auto mb-4 pr-1">
      
      <!-- Welcome Message -->
      <div class="flex gap-3 msg-anim">
        <div class="w-8 h-8 rounded-lg bg-slate-900 p-1 border border-emerald-500/50 shadow-md flex items-center justify-center flex-shrink-0">
          <img src="/img/logo%20IA%20bits.png" alt="AI Bits" class="w-full h-full object-contain">
        </div>
        <div class="rounded-2xl rounded-tl-sm p-4 max-w-[88%] shadow-md transition-colors message-ai-box">
          <p class="text-sm leading-relaxed">
            👋 Olá! Eu sou a <strong>AI Bits</strong>, assistente de inteligência artificial oficial do <strong>EduConecta Periferia</strong>!
          </p>
          <p class="text-xs mt-2 opacity-85">
            Estou aqui para tirar dúvidas sobre como usar o aplicativo, como agendar aulas de reforço ou como resolver eventuais problemas na leitura da sua conta de luz ou água (<strong>Enel, Sabesp ou Claro</strong>).
          </p>
          
          <!-- Quick Action Buttons -->
          <div class="flex flex-wrap gap-2 mt-3 pt-2 border-t border-slate-700/40" id="quick-buttons-box">
            <button onclick="quickAsk('Enviei a foto da conta da Enel e deu erro no endereço. O que fazer?')" class="text-xs font-medium px-3 py-1.5 rounded-lg border transition quick-btn">
              📸 Erro ao enviar conta da Enel
            </button>
            <button onclick="quickAsk('Como faço para marcar aula de reforço de matemática?')" class="text-xs font-medium px-3 py-1.5 rounded-lg border transition quick-btn">
              📚 Agendar aula de matemática
            </button>
            <button onclick="quickAsk('O que é o projeto EduConecta Periferia?')" class="text-xs font-medium px-3 py-1.5 rounded-lg border transition quick-btn">
              💡 O que é o EduConecta?
            </button>
          </div>
        </div>
      </div>

    </div>

    <!-- Input Area -->
    <div class="rounded-2xl p-2.5 shadow-xl border transition-colors input-container-box">
      <form id="chat-form" onsubmit="sendMessage(event)" class="flex gap-2 items-center">
        <input 
          id="user-input"
          type="text" 
          placeholder="Digite sua dúvida sobre o aplicativo..." 
          class="flex-1 bg-transparent px-3 py-2 text-sm focus:outline-none placeholder-slate-400"
          autocomplete="off"
        />
        <button 
          id="send-btn"
          type="submit" 
          title="Enviar mensagem"
          class="w-10 h-10 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center transition shadow-md shadow-emerald-600/20 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0">
          <i class="fa-solid fa-paper-plane text-sm"></i>
        </button>
      </form>
    </div>
  </main>

  <!-- Footer -->
  <footer id="main-footer" class="text-center py-2.5 text-xs border-t transition-colors text-slate-500 border-slate-800 bg-slate-900/60">
    EduConecta Periferia - Inclusão Digital e Apoio Escolar (ODS 4 & 10)
  </footer>

  <script>
    const messagesContainer = document.getElementById('chat-messages');
    const inputField = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    
    // Theme Management
    let currentTheme = localStorage.getItem('theme') || 'dark';

    function applyTheme(theme) {
      currentTheme = theme;
      localStorage.setItem('theme', theme);
      
      const body = document.getElementById('body-root');
      const header = document.getElementById('main-header');
      const headerTitle = document.getElementById('header-title');
      const headerTeam = document.getElementById('header-team');
      const footer = document.getElementById('main-footer');
      const themeIcon = document.getElementById('theme-icon');
      const themeText = document.getElementById('theme-text');
      const themeBtn = document.getElementById('theme-toggle-btn');
      const educonectaBadge = document.getElementById('educonecta-badge');
      const inputContainer = document.querySelector('.input-container-box');

      if (theme === 'light') {
        // MODO CLARO: Topo verde da marca, fundo claro, alto contraste
        document.documentElement.classList.remove('dark');
        body.className = "min-h-screen flex flex-col font-sans transition-colors duration-200 bg-slate-100 text-slate-800";
        header.className = "border-b transition-colors duration-200 sticky top-0 z-50 px-4 py-3 bg-gradient-to-r from-emerald-800 to-green-700 text-white shadow-md border-emerald-900/30";
        headerTitle.className = "font-bold text-lg leading-tight flex items-center gap-2 text-white";
        headerTeam.className = "text-xs text-emerald-100";
        footer.className = "text-center py-2.5 text-xs border-t transition-colors text-slate-600 border-slate-300 bg-slate-200/80";
        
        themeIcon.className = "fa-solid fa-sun text-amber-300";
        themeText.innerText = "Modo Claro";
        themeBtn.className = "flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-xl border transition shadow-sm bg-emerald-900/60 hover:bg-emerald-900 border-emerald-600/50 text-white";
        if (educonectaBadge) {
          educonectaBadge.className = "text-xs font-semibold px-3 py-1 rounded-full border transition-colors shadow-sm bg-emerald-900/80 text-white border-emerald-500/50 tracking-wide";
        }
        
        inputContainer.className = "rounded-2xl p-2.5 shadow-md border transition-colors input-container-box bg-white border-slate-300 text-slate-800";
      } else {
        // MODO ESCURO: Preto profundo e verde escuro da marca
        document.documentElement.classList.add('dark');
        body.className = "min-h-screen flex flex-col font-sans transition-colors duration-200 bg-slate-950 text-slate-100";
        header.className = "border-b transition-colors duration-200 sticky top-0 z-50 px-4 py-3 bg-slate-900 border-emerald-900/50 shadow-md";
        headerTitle.className = "font-bold text-lg leading-tight flex items-center gap-2 text-white";
        headerTeam.className = "text-xs text-slate-400";
        footer.className = "text-center py-2.5 text-xs border-t transition-colors text-slate-500 border-slate-800 bg-slate-900/60";
        
        themeIcon.className = "fa-solid fa-moon text-cyan-300";
        themeText.innerText = "Modo Escuro";
        themeBtn.className = "flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-xl border transition shadow-sm bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200";
        if (educonectaBadge) {
          educonectaBadge.className = "text-xs font-semibold px-3 py-1 rounded-full border transition-colors shadow-sm bg-emerald-950/80 text-emerald-300 border-emerald-700/50 tracking-wide";
        }
        
        inputContainer.className = "rounded-2xl p-2.5 shadow-xl border transition-colors input-container-box bg-slate-900 border-slate-800 text-slate-100";
      }

      // Atualiza balões existentes
      updateMessageStyles();
    }

    function toggleTheme() {
      applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
    }

    function updateMessageStyles() {
      const isDark = currentTheme === 'dark';
      
      // Balões da IA
      document.querySelectorAll('.message-ai-box').forEach(el => {
        el.className = isDark 
          ? "rounded-2xl rounded-tl-sm p-4 max-w-[88%] shadow-md transition-colors message-ai-box bg-slate-900 text-slate-100 border border-slate-800"
          : "rounded-2xl rounded-tl-sm p-4 max-w-[88%] shadow-md transition-colors message-ai-box bg-white text-slate-800 border border-slate-200";
      });

      // Balões do Usuário
      document.querySelectorAll('.message-user-box').forEach(el => {
        el.className = isDark
          ? "rounded-2xl rounded-tr-sm p-3.5 max-w-[85%] text-sm shadow-md transition-colors message-user-box bg-emerald-900 text-emerald-50 border border-emerald-800/60"
          : "rounded-2xl rounded-tr-sm p-3.5 max-w-[85%] text-sm shadow-md transition-colors message-user-box bg-emerald-700 text-white";
      });

      // Botões rápidos
      document.querySelectorAll('.quick-btn').forEach(el => {
        el.className = isDark
          ? "text-xs font-medium px-3 py-1.5 rounded-lg border transition quick-btn bg-slate-800 hover:bg-slate-700 text-emerald-400 border-slate-700"
          : "text-xs font-medium px-3 py-1.5 rounded-lg border transition quick-btn bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-200";
      });
    }

    function quickAsk(text) {
      inputField.value = text;
      document.getElementById('chat-form').dispatchEvent(new Event('submit'));
    }

    async function sendMessage(e) {
      e.preventDefault();
      const text = inputField.value.trim();
      if (!text) return;

      inputField.value = '';
      sendBtn.disabled = true;

      // Render User Message
      appendUserMessage(text);

      // Render Loading Message
      const loadingId = appendLoading();
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mensagem: text })
        });
        const data = await response.json();
        removeLoading(loadingId);

        if (data.error) {
          appendAiErrorMessage('Ops! Tive um problema ao processar. Detalhes: ' + data.error);
        } else {
          appendAssistantResponse(data);
        }
      } catch (err) {
        removeLoading(loadingId);
        appendAiErrorMessage('Erro de conexão com o servidor local: ' + err.message);
      } finally {
        sendBtn.disabled = false;
        inputField.focus();
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }

    function appendUserMessage(text) {
      const isDark = currentTheme === 'dark';
      const div = document.createElement('div');
      div.className = 'flex gap-3 justify-end msg-anim';
      div.innerHTML = `
        <div class="p-3.5 max-w-[85%] text-sm shadow-md transition-colors message-user-box rounded-2xl rounded-tr-sm ${isDark ? 'bg-emerald-900 text-emerald-50 border border-emerald-800/60' : 'bg-emerald-700 text-white'}">
          <p class="leading-relaxed">${escapeHtml(text)}</p>
        </div>
        <div class="w-8 h-8 rounded-lg ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-300 text-slate-700'} flex-shrink-0 flex items-center justify-center text-xs font-bold shadow-sm">
          <i class="fa-solid fa-user"></i>
        </div>
      `;
      messagesContainer.appendChild(div);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendAssistantResponse(data) {
      const isDark = currentTheme === 'dark';
      const div = document.createElement('div');
      div.className = 'flex gap-3 msg-anim';

      let passosHtml = '';
      if (data.passos_para_solucao && data.passos_para_solucao.length > 0) {
        passosHtml = `
          <div class="mt-3.5 pt-3 border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}">
            <p class="text-xs font-semibold ${isDark ? 'text-emerald-400' : 'text-emerald-700'} uppercase tracking-wider mb-2">Passo a passo recomendado:</p>
            <ol class="space-y-2 text-xs">
              ${data.passos_para_solucao.map((p, i) => `
                <li class="flex items-start gap-2.5">
                  <span class="w-4 h-4 rounded-full ${isDark ? 'bg-emerald-500/20 text-emerald-300' : 'bg-emerald-100 text-emerald-800'} font-bold flex items-center justify-center flex-shrink-0 text-[10px] mt-0.5">${i+1}</span>
                  <span class="leading-relaxed ${isDark ? 'text-slate-200' : 'text-slate-700'}">${escapeHtml(p)}</span>
                </li>
              `).join('')}
            </ol>
          </div>
        `;
      }

      div.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-slate-900 p-1 border border-emerald-500/50 shadow-md flex items-center justify-center flex-shrink-0">
          <img src="/img/logo%20IA%20bits.png" alt="AI Bits" class="w-full h-full object-contain">
        </div>
        <div class="rounded-2xl rounded-tl-sm p-4 max-w-[88%] shadow-md transition-colors message-ai-box ${isDark ? 'bg-slate-900 text-slate-100 border border-slate-800' : 'bg-white text-slate-800 border border-slate-200'}">
          <p class="text-sm leading-relaxed">${escapeHtml(data.resposta_humanizada)}</p>
          ${passosHtml}
        </div>
      `;
      messagesContainer.appendChild(div);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendAiErrorMessage(text) {
      const isDark = currentTheme === 'dark';
      const div = document.createElement('div');
      div.className = 'flex gap-3 msg-anim';
      div.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-slate-900 p-1 border border-rose-500/50 shadow-md flex items-center justify-center flex-shrink-0">
          <img src="/img/logo%20IA%20bits.png" alt="AI Bits" class="w-full h-full object-contain">
        </div>
        <div class="rounded-2xl rounded-tl-sm p-3.5 max-w-[85%] text-sm shadow-md bg-rose-950/40 border border-rose-800/60 text-rose-200">
          <p class="leading-relaxed">${escapeHtml(text)}</p>
        </div>
      `;
      messagesContainer.appendChild(div);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendLoading() {
      const isDark = currentTheme === 'dark';
      const id = 'loading-' + Date.now();
      const div = document.createElement('div');
      div.id = id;
      div.className = 'flex gap-3 msg-anim';
      div.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-slate-900 p-1 border border-emerald-500/50 shadow-md flex items-center justify-center flex-shrink-0">
          <img src="/img/logo%20IA%20bits.png" alt="AI Bits" class="w-full h-full object-contain animate-pulse">
        </div>
        <div class="rounded-2xl rounded-tl-sm p-3.5 max-w-[85%] text-sm flex items-center gap-2.5 shadow-sm ${isDark ? 'bg-slate-900 border border-slate-800 text-slate-400' : 'bg-white border border-slate-200 text-slate-500'}">
          <i class="fa-solid fa-circle-notch fa-spin text-emerald-500"></i>
          <span>AI Bits está pensando...</span>
        </div>
      `;
      messagesContainer.appendChild(div);
      return id;
    }

    function removeLoading(id) {
      const el = document.getElementById(id);
      if (el) el.remove();
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.innerText = text;
      return div.innerHTML;
    }

    // Inicialização de tema salvo
    document.addEventListener('DOMContentLoaded', () => {
      applyTheme(currentTheme);
    });
  </script>
</body>
</html>
"""

class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Rota raiz: serve o HTML
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        # 2. Servir arquivos estáticos (img, icon, favicon)
        # Decodifica URL encoding (ex: %20 para espaço)
        clean_path = urllib.parse.unquote(self.path).lstrip("/")
        
        # Redirecionamento de conveniência para favicons na raiz
        if clean_path in ["favicon.ico", "apple-touch-icon.png"]:
            clean_path = os.path.join("img", "icon", clean_path)

        full_path = os.path.normpath(os.path.join(BASE_DIR, clean_path))

        # Medida de segurança: proibir path traversal fora do diretório GAE
        if not full_path.startswith(BASE_DIR) or not os.path.exists(full_path) or os.path.isdir(full_path):
            self.send_response(404)
            self.end_headers()
            return

        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            if full_path.endswith(".ico"):
                mime_type = "image/x-icon"
            elif full_path.endswith(".webmanifest"):
                mime_type = "application/manifest+json"
            else:
                mime_type = "application/octet-stream"

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_response(500)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                mensagem = data.get("mensagem", "")
                resultado = tirar_duvida_helper(mensagem)
                response_data = resultado.model_dump()
                status_code = 200
            except Exception as e:
                response_data = {"error": str(e)}
                status_code = 500

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, ChatHandler)
    url = f"http://localhost:{PORT}"
    print("=" * 65)
    print(f"🚀 AI Bits Web App rodando em: {url}")
    print(f"🎨 Identidade Visual: AI Bits - EduConecta Periferia")
    print(f"🌓 Temas: Modo Claro (Verde Marca) & Modo Escuro (Preto/Verde)")
    print("Pressione Ctrl+C para encerrar o servidor.")
    print("=" * 65)
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado com sucesso.")

if __name__ == "__main__":
    run()
