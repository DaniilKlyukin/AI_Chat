let savedSessionId = localStorage.getItem('primat_session_id');

if (!savedSessionId) {
    savedSessionId = "session_" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('primat_session_id', savedSessionId);
}

const CONFIG = {
    API_BASE: window.location.origin,
    SESSION_ID: savedSessionId
};

const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const loader = document.getElementById('loader');

async function loadHistory() {
    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/chat/history?session_id=${CONFIG.SESSION_ID}`);
        const data = await res.json();

        if (data.status === 'success' && data.history.length > 0) {
            chatContainer.innerHTML = `
                <div class="flex justify-center my-4">
                    <span class="bg-[#86a9c9] px-4 py-0.5 rounded-full text-[12px] text-white font-medium shadow-sm">
                        Сегодня
                    </span>
                </div>
            `;
            data.history.forEach(msg => {
                appendMessage(msg.role, msg.content, false);
            });
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (err) {}
}

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

function appendMessage(role, content, animate = true) {
    const isUser = role === 'user';
    const wrapper = document.createElement('div');
    wrapper.className = `flex w-full ${isUser ? 'justify-end' : 'justify-start'} ${animate ? 'animate-msg' : ''} px-2`;

    const bubble = document.createElement('div');
    bubble.className = `relative max-w-[85%] md:max-w-[75%] px-3 py-2 rounded-[15px] shadow-sm message-bubble ${
        isUser
        ? 'bg-[#effdde] text-slate-800 rounded-tr-[4px]'
        : 'bg-white text-slate-800 rounded-tl-[4px]'
    }`;

    const text = document.createElement('div');
    text.className = "prose prose-slate prose-sm max-w-none text-[15px]";
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
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';
    userInput.style.height = 'auto';
    loader.classList.remove('hidden');

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: text,
                session_id: CONFIG.SESSION_ID
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            appendMessage('assistant', data.response);
        }
    } catch (err) {
    } finally {
        loader.classList.add('hidden');
    }
});

document.getElementById('clear-btn').addEventListener('click', async () => {
    if(confirm("Очистить чат?")) {
        await fetch(`${CONFIG.API_BASE}/api/system/clear-history?session_id=${CONFIG.SESSION_ID}`, {method: 'POST'});
        chatContainer.innerHTML = `
            <div class="flex justify-center my-4">
                <span class="bg-[#86a9c9] px-4 py-0.5 rounded-full text-[12px] text-white font-medium shadow-sm">
                    Сегодня
                </span>
            </div>
        `;
    }
});

loadHistory();