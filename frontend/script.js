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
const fileInput = document.getElementById('file-input');
const attachBtn = document.getElementById('attach-btn');
const filePreviewContainer = document.getElementById('file-preview-container');
const dropOverlay = document.getElementById('drop-overlay');

let selectedFiles = [];

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

function updateFilePreview() {
    filePreviewContainer.innerHTML = '';
    if (selectedFiles.length > 0) {
        filePreviewContainer.classList.remove('hidden');
        filePreviewContainer.classList.add('flex');
        selectedFiles.forEach((file, index) => {
            const pill = document.createElement('div');
            pill.className = 'flex items-center gap-2 bg-white border border-[#c8d7e6] rounded-full px-3 py-1 text-sm text-slate-700 shadow-sm';
            pill.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-[#50a2e9]">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <span class="max-w-[150px] truncate">${file.name}</span>
                <button type="button" class="text-slate-400 hover:text-red-500" onclick="removeFile(${index})">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
                        <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                    </svg>
                </button>
            `;
            filePreviewContainer.appendChild(pill);
        });
    } else {
        filePreviewContainer.classList.add('hidden');
        filePreviewContainer.classList.remove('flex');
    }
}

window.removeFile = function(index) {
    selectedFiles.splice(index, 1);
    updateFilePreview();
};

attachBtn.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    Array.from(e.target.files).forEach(file => {
        selectedFiles.push(file);
    });
    updateFilePreview();
    fileInput.value = '';
});

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

let dragCounter = 0;

document.body.addEventListener('dragenter', (e) => {
    dragCounter++;
    dropOverlay.classList.remove('hidden');
});

document.body.addEventListener('dragleave', (e) => {
    dragCounter--;
    if (dragCounter === 0) {
        dropOverlay.classList.add('hidden');
    }
});

document.body.addEventListener('drop', (e) => {
    dragCounter = 0;
    dropOverlay.classList.add('hidden');
    let dt = e.dataTransfer;
    let files = dt.files;
    Array.from(files).forEach(file => {
        selectedFiles.push(file);
    });
    updateFilePreview();
});

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
    if (!text && selectedFiles.length === 0) return;

    let displayHtml = text;
    if (selectedFiles.length > 0) {
        const fileNames = selectedFiles.map(f => `📎 ${f.name}`).join('<br>');
        displayHtml = displayHtml ? `${displayHtml}<br><br><span class="text-sm text-slate-500">${fileNames}</span>` : `<span class="text-sm text-slate-500">${fileNames}</span>`;
    }

    appendMessage('user', displayHtml);

    const formData = new FormData();
    formData.append('message', text || 'Посмотри прикрепленные файлы.');
    formData.append('session_id', CONFIG.SESSION_ID);
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    userInput.value = '';
    userInput.style.height = 'auto';
    selectedFiles = [];
    updateFilePreview();
    loader.classList.remove('hidden');

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/chat`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.status === 'success') {
            appendMessage('assistant', data.response);

            if (data.download_url) {
                const downloadLink = document.createElement('div');
                downloadLink.className = 'mt-3 p-3 bg-[#50a2e9]/10 border border-[#50a2e9]/30 rounded-lg flex items-center justify-between';
                downloadLink.innerHTML = `
                    <div class="flex items-center gap-2">
                        <svg class="w-5 h-5 text-[#50a2e9]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        <span class="text-sm font-medium">Проект готов к загрузке</span>
                    </div>
                    <a href="${data.download_url}" download class="text-[12px] bg-[#50a2e9] text-white px-3 py-1 rounded-md hover:bg-[#4392d8] transition">Скачать ZIP</a>
                `;
                const lastBubble = chatContainer.lastElementChild.querySelector('.message-bubble');
                lastBubble.appendChild(downloadLink);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
    } catch (err) {
        console.error(err);
    } finally {
        loader.classList.add('hidden');
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text && selectedFiles.length === 0) return;

    let displayHtml = text;
    if (selectedFiles.length > 0) {
        const fileNames = selectedFiles.map(f => `📎 ${f.name}`).join('<br>');
        displayHtml = displayHtml ? `${displayHtml}<br><br><span class="text-sm text-slate-500">${fileNames}</span>` : `<span class="text-sm text-slate-500">${fileNames}</span>`;
    }

    appendMessage('user', displayHtml);

    const formData = new FormData();
    formData.append('message', text || 'Посмотри прикрепленные файлы.');
    formData.append('session_id', CONFIG.SESSION_ID);
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    userInput.value = '';
    userInput.style.height = 'auto';
    selectedFiles = [];
    updateFilePreview();
    loader.classList.remove('hidden');

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/chat`, {
            method: 'POST',
            body: formData
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