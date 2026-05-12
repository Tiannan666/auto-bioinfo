// Bioinformatics Analysis Chat — Frontend Logic

let isWaiting = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  checkConfig();
  document.getElementById('userInput').focus();
});

// Check API key status
async function checkConfig() {
  try {
    const res = await fetch('/api/config/status');
    const data = await res.json();
    const statusEl = document.getElementById('keyStatus');
    if (data.has_key) {
      statusEl.innerHTML = '<span style="color:var(--accent)">●</span> API 已配置';
    } else {
      statusEl.innerHTML = '<span style="color:#f59e0b">●</span> 未配置 API Key';
      openSettings();
    }
  } catch (e) {
    console.error('Config check failed:', e);
  }
}

// Settings modal
function openSettings() {
  document.getElementById('settingsModal').classList.add('active');
  document.getElementById('apiKey').focus();
  document.getElementById('saveStatus').style.display = 'none';
}
function closeSettings() {
  document.getElementById('settingsModal').classList.remove('active');
}

async function saveSettings() {
  const key = document.getElementById('apiKey').value.trim();
  if (!key) return;

  const statusEl = document.getElementById('saveStatus');
  statusEl.style.display = 'block';
  statusEl.textContent = '保存中...';
  statusEl.className = 'status';

  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deepseek_api_key: key }),
    });
    if (res.ok) {
      statusEl.textContent = '保存成功!';
      statusEl.className = 'status';
      document.getElementById('keyStatus').innerHTML =
        '<span style="color:var(--accent)">●</span> API 已配置';
      setTimeout(closeSettings, 800);
    } else {
      statusEl.textContent = '保存失败';
      statusEl.className = 'status error';
    }
  } catch (e) {
    statusEl.textContent = '网络错误: ' + e.message;
    statusEl.className = 'status error';
  }
}

// Send a message
async function sendMessage() {
  if (isWaiting) return;

  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  // Hide welcome
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.style.display = 'none';

  // Add user message to chat
  appendMessage('user', text);
  input.value = '';
  input.style.height = 'auto';

  // Add loading placeholder
  const loadingMsg = appendMessage('assistant', '', true);
  const loadingEl = loadingMsg.querySelector('.msg-content');

  isWaiting = true;
  document.getElementById('sendBtn').disabled = true;

  try {
    // Collect conversation history
    const messages = collectHistory();

    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages }),
    });

    const data = await res.json();

    // Remove loading
    loadingMsg.remove();

    // Render response
    if (data.message) {
      const content = fixImagePaths(data.message.content);
      appendMessage('assistant', content);
    }

    // Show execution results
    if (data.executions && data.executions.length > 0) {
      for (const exec of data.executions) {
        if (exec.output && !exec.output.includes('Script executed successfully')) {
          // Output already included in message content, handled by backend
        }
      }
    }
  } catch (e) {
    loadingMsg.remove();
    appendMessage('assistant', '**网络错误**: ' + e.message);
  } finally {
    isWaiting = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('userInput').focus();
  }
}

// Send a hint as a message
function sendHint(text) {
  document.getElementById('userInput').value = text;
  sendMessage();
}

// Append a message to the chat
function appendMessage(role, content, isLoading) {
  const container = document.getElementById('chatContainer');
  const div = document.createElement('div');
  div.className = `message ${role}`;

  const roleLabel = role === 'user' ? '你' : '生信助手';
  const roleClass = role === 'user' ? 'user' : 'assistant';

  let roleHTML = `<div class="role">${roleLabel}</div>`;

  let contentHTML = '';
  if (isLoading) {
    contentHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
  } else {
    contentHTML = renderMarkdown(content);
  }

  div.innerHTML = roleHTML + `<div class="msg-content">${contentHTML}</div>`;
  container.appendChild(div);
  scrollToBottom();
  return div;
}

// Render markdown with marked.js
function renderMarkdown(text) {
  if (typeof marked === 'undefined') {
    return `<pre>${escapeHtml(text)}</pre>`;
  }
  marked.setOptions({
    breaks: true,
    gfm: true,
  });
  const html = marked.parse(text);
  return html;
}

// Fix image paths from output/xxx.png to /output/xxx.png
function fixImagePaths(text) {
  return text.replace(/\(output\//g, '(/output/');
}

// Collect conversation history from the DOM
function collectHistory() {
  const messages = [];
  const msgElements = document.querySelectorAll('.message');
  msgElements.forEach(el => {
    const roleEl = el.querySelector('.role');
    const contentEl = el.querySelector('.msg-content');
    if (!roleEl || !contentEl) return;

    const role = roleEl.textContent.trim() === '你' ? 'user' : 'assistant';
    // Get raw text content (strip HTML tags for image paths etc.)
    let content = '';
    const imgs = contentEl.querySelectorAll('img');
    contentEl.querySelectorAll('img').forEach(img => {
      img.replaceWith(img.getAttribute('alt') || '[Image]');
    });
    content = contentEl.textContent.trim();
    if (content) {
      messages.push({ role, content });
    }
  });
  return messages;
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

function scrollToBottom() {
  const container = document.getElementById('chatContainer');
  container.scrollTop = container.scrollHeight;
}
