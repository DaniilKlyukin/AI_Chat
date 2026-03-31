let savedSessionId = localStorage.getItem('primat_session_id') || "session_" + Math.random().toString(36).substr(2, 9);
localStorage.setItem('primat_session_id', savedSessionId);

const CONFIG = { API_BASE: window.location.origin, SESSION_ID: savedSessionId };
const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const loader = document.getElementById('loader');
const fileInput = document.getElementById('file-input');
const attachBtn = document.getElementById('attach-btn');
const filePreviewContainer = document.getElementById('file-preview-container');
const modelSelect = document.getElementById('model-select');
const sendBtn = document.getElementById('send-btn');
const sendIcon = document.getElementById('send-icon');
const timerDisplay = document.getElementById('timer-display');

let selectedFiles = [];
let cooldownTimer = null;

function startCooldown(seconds) {
    clearInterval(cooldownTimer);
    sendBtn.disabled = true;
    sendIcon.classList.add('hidden');
    timerDisplay.classList.remove('hidden');

    let timeLeft = seconds;
    timerDisplay.innerText = timeLeft;

    cooldownTimer = setInterval(() => {
        timeLeft--;
        timerDisplay.innerText = timeLeft;
        if (timeLeft <= 0) {
            clearInterval(cooldownTimer);
            sendBtn.disabled = false;
            sendIcon.classList.remove('hidden');
            timerDisplay.classList.add('hidden');
        }
    }, 1000);
}

async function loadHistory() {
    const res = await fetch(`${CONFIG.API_BASE}/api/chat/history?session_id=${CONFIG.SESSION_ID}`);
    const data = await res.json();
    if (data.status === 'success') {
        chatContainer.innerHTML = '';
        data.history.forEach(msg => appendMessage(msg.role, msg.content, false));
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function updateFilePreview() {
    filePreviewContainer.innerHTML = '';
    if (selectedFiles.length > 0) {
        filePreviewContainer.classList.replace('hidden', 'flex');
        selectedFiles.forEach((file, index) => {
            const pill = document.createElement('div');
            pill.className = 'flex items-center gap-2 bg-white border rounded-full px-3 py-1 text-sm shadow-sm';
            pill.innerHTML = `<span class="max-w-[150px] truncate">${file.name}</span><button type="button" class="hover:text-red-500" onclick="removeFile(${index})">×</button>`;
            filePreviewContainer.appendChild(pill);
        });
    } else {
        filePreviewContainer.classList.replace('flex', 'hidden');
    }
}

window.removeFile = (index) => { selectedFiles.splice(index, 1); updateFilePreview(); };
attachBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => { Array.from(e.target.files).forEach(f => selectedFiles.push(f)); updateFilePreview(); });

userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

function appendMessage(role, content, animate = true) {
    const isUser = role === 'user';
    const isSummary = content.startsWith("[Контекст");
    const wrapper = document.createElement('div');
    wrapper.className = `flex w-full ${isUser ? 'justify-end' : 'justify-start'} px-2`;

    const bubble = document.createElement('div');
    bubble.className = `max-w-[85%] px-3 py-2 rounded-[15px] shadow-sm ${isUser ? 'bg-[#effdde]' : 'bg-white'} ${isSummary ? 'opacity-60 italic text-xs' : ''}`;

    const text = document.createElement('div');
    text.className = "prose prose-sm max-w-none text-[15px]";
    text.innerHTML = isUser ? content.replace(/\n/g, '<br>') : marked.parse(content);
    bubble.appendChild(text);
    wrapper.appendChild(bubble);
    chatContainer.appendChild(wrapper);
    bubble.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text && selectedFiles.length === 0) return;

    appendMessage('user', text || "Файлы...");
    const formData = new FormData();
    formData.append('message', text || 'Посмотри файлы');
    formData.append('session_id', CONFIG.SESSION_ID);
    formData.append('model_id', modelSelect.value);
    selectedFiles.forEach(f => formData.append('files', f));

    userInput.value = '';
    userInput.style.height = 'auto';
    const filesSnap = [...selectedFiles];
    selectedFiles = [];
    updateFilePreview();
    loader.classList.remove('hidden');

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/chat`, { method: 'POST', body: formData });
        const data = await res.json();

        if (data.response.startsWith("ЛИМИТ:")) {
            const sec = parseInt(data.response.split(":")[1]);
            startCooldown(sec);
            chatContainer.lastElementChild.remove();
            selectedFiles = filesSnap;
            updateFilePreview();
        } else {
            await loadHistory();
            const cd = data.model_used.includes("gemini") ? 180 : 15;
            startCooldown(cd);
        }
    } catch (err) {
        console.error(err);
    } finally {
        loader.classList.add('hidden');
    }
});

document.getElementById('clear-btn').addEventListener('click', async () => {
    if(confirm("Очистить историю?")) {
        await fetch(`${CONFIG.API_BASE}/api/system/clear-history?session_id=${CONFIG.SESSION_ID}`, {method: 'POST'});
        location.reload();
    }
});

loadHistory();