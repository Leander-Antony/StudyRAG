/**
 * Chat screen - Main interaction with StudyRAG
 */

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const uploadBtn = document.getElementById('uploadBtn');
const modeBtn = document.getElementById('modeBtn');
const modeSelector = document.getElementById('modeSelector');
const uploadModal = document.getElementById('uploadModal');
const uploadForm = document.getElementById('uploadForm');
const uploadStatus = document.getElementById('uploadStatus');
const sessionNameEl = document.getElementById('sessionName');
const uploadModalClose = document.querySelector('.modal-close');
const sessionSelect = document.getElementById('sessionSelect');
const filesList = document.getElementById('filesList');
const filesCount = document.getElementById('filesCount');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');

// State
let currentSessionId = null;
let currentMode = 'chat';
let currentSession = null;
let historyLoaded = false;
let sessionsCache = [];

// Loader functions
function showLoader(text = 'Processing...') {
    if (loadingOverlay && loadingText) {
        loadingText.textContent = text;
        loadingOverlay.style.display = 'flex';
    }
}

function hideLoader() {
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initializeSession();
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    uploadBtn.addEventListener('click', openUploadModal);
    modeBtn.addEventListener('click', toggleModeSelector);
    const pdfBtn = document.getElementById('pdfBtn');
    if (pdfBtn) pdfBtn.addEventListener('click', exportChatToPDF);
    uploadForm.addEventListener('submit', handleUpload);
    uploadModalClose.addEventListener('click', closeUploadModal);

    // Mode buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => setMode(btn.dataset.mode));
    });

    // Session switcher
    if (sessionSelect) {
        sessionSelect.addEventListener('change', (e) => switchSession(e.target.value));
    }

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === uploadModal) {
            closeUploadModal();
        }
    });
}

function initializeSession() {
    const urlParams = new URLSearchParams(window.location.search);
    currentSessionId = urlParams.get('session_id');

    loadSessionListAndSelect();
}

async function loadSessionListAndSelect() {
    try {
        sessionsCache = await StudyRAGAPI.getSessions();

        if (!sessionsCache || sessionsCache.length === 0) {
            addSystemMessage('No sessions found. Please create one first.');
            window.location.href = 'index.html';
            return;
        }

        populateSessionSelect(sessionsCache);

        // If no session_id in URL, default to first session
        if (!currentSessionId) {
            currentSessionId = sessionsCache[0].session_id;
        }

        // Ensure select shows current session
        if (sessionSelect) {
            sessionSelect.value = currentSessionId;
        }

        await loadSessionInfo();
        await loadFiles();
    } catch (error) {
        addSystemMessage(`Error loading sessions: ${error.message}`);
        console.error('Error loading session list', error);
    }
}

function populateSessionSelect(sessions) {
    if (!sessionSelect) return;
    sessionSelect.innerHTML = '';
    sessions.forEach(sess => {
        const opt = document.createElement('option');
        opt.value = sess.session_id;
        opt.textContent = `${sess.name}`;
        sessionSelect.appendChild(opt);
    });
}

async function loadSessionInfo() {
    try {
        const session = await StudyRAGAPI.getSession(currentSessionId);
        currentSession = session;
        sessionNameEl.textContent = session.name;
        
        // Load chat history from the session
        loadChatHistory(session);
        
        const lastUsed = session.last_used ? new Date(session.last_used).toLocaleString() : 'Never used';
        addSystemMessage(`✓ Session loaded. Last used: ${lastUsed}`);
        await loadFiles();
    } catch (error) {
        sessionNameEl.textContent = 'Error loading session';
        addSystemMessage(`Error loading session: ${error.message}`);
    }
}

async function switchSession(newSessionId) {
    if (!newSessionId || newSessionId === currentSessionId) return;
    currentSessionId = newSessionId;
    historyLoaded = false;
    currentSession = null;

    // Clear chat UI
    chatMessages.innerHTML = '';
    addSystemMessage('Switched session. Loading history...');

    // Update URL without reload
    const params = new URLSearchParams(window.location.search);
    params.set('session_id', currentSessionId);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);

    await loadSessionInfo();
}

function loadChatHistory(session) {
    /**
     * Load chat history from the session's history file
     * This displays previous messages when reopening a session
     */
    try {
        // Fetch and display previous chat history
        StudyRAGAPI.getChatHistory(currentSessionId).then(data => {
            if (data.messages && data.messages.length > 0) {
                // Clear the initial system message
                chatMessages.innerHTML = '';
                
                // Restore previous messages
                data.messages.forEach(msg => {
                    if (msg.role === 'user') {
                        addUserMessage(msg.content, true);
                    } else if (msg.role === 'assistant') {
                        addAssistantMessage(msg.content, true);
                    }
                });
                
                addSystemMessage(`✓ Restored ${data.messages.length} previous messages`);
            }
        }).catch(err => {
            console.error('Error fetching chat history:', err);
        });
        
        historyLoaded = true;
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

async function loadFiles() {
    if (!filesList || !filesCount || !currentSessionId) return;
    filesList.innerHTML = '<p class="loading">Loading files...</p>';
    try {
        const files = await StudyRAGAPI.getSessionFiles(currentSessionId);
        filesCount.textContent = files.length;

        if (!files || files.length === 0) {
            filesList.innerHTML = '<p class="loading">No files yet.</p>';
            return;
        }

        filesList.innerHTML = '';
        files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            const created = file.created_at ? new Date(file.created_at).toLocaleString() : '';
            item.innerHTML = `
                <div>${escapeHtml(file.filename)}</div>
                <div class="meta">${file.category} • ${file.chunks_count || 0} chunks ${created ? '• ' + created : ''}</div>
            `;
            filesList.appendChild(item);
        });
    } catch (error) {
        filesList.innerHTML = `<p class="loading" style="color:#ef4444;">Error loading files: ${error.message}</p>`;
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) return;

    // Add user message to UI
    addUserMessage(message);
    messageInput.value = '';
    sendBtn.disabled = true;

    try {
        // Send to API
        const response = await StudyRAGAPI.chat(currentSessionId, message, currentMode);
        
        // Add assistant response
        addAssistantMessage(response.response);
    } catch (error) {
        addSystemMessage(`Error: ${error.message}`);
    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

function setMode(mode) {
    currentMode = mode;
    
    // Update UI
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
    
    addSystemMessage(`Mode changed to: ${mode}`);
}

function toggleModeSelector() {
    modeSelector.style.display = modeSelector.style.display === 'none' ? 'flex' : 'none';
}

function openUploadModal() {
    uploadModal.classList.add('open');
    document.getElementById('fileInput').focus();
}

function closeUploadModal() {
    uploadModal.classList.remove('open');
    uploadForm.reset();
    uploadStatus.classList.remove('show', 'success', 'error');
}

async function handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const category = document.getElementById('uploadCategory').value;
    const file = fileInput.files[0];

    if (!file) {
        showUploadStatus('Please select a file', 'error');
        return;
    }

    const uploadBtn = uploadForm.querySelector('button[type="submit"]');
    uploadBtn.disabled = true;
    showUploadStatus('Uploading...', 'info');
    showLoader(`Extracting text from ${file.name}...`);

    try {
        const response = await StudyRAGAPI.uploadDocument(currentSessionId, file, category);
        hideLoader();
        
        if (response.status === 'completed') {
            showUploadStatus(`✓ Uploaded "${response.filename}" (${response.chunks_count} chunks)`, 'success');
            uploadForm.reset();
            setTimeout(closeUploadModal, 1500);
            addSystemMessage(`Document uploaded: ${response.filename}`);
            loadFiles();
        } else {
            showUploadStatus(`Error: ${response.message}`, 'error');
        }
    } catch (error) {
        hideLoader();
        showUploadStatus(`Error: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
    }
}

function showUploadStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.classList.add('show', type);
    
    if (type === 'success') {
        setTimeout(() => {
            uploadStatus.classList.remove('show', type);
        }, 3000);
    }
}

// Message UI helpers
function addUserMessage(content, isRestore = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user';
    msgDiv.innerHTML = `<p>${escapeHtml(content)}</p>`;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function addAssistantMessage(content, isRestore = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    msgDiv.innerHTML = `<p>${formatMessage(content)}</p>`;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function addSystemMessage(content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message system';
    msgDiv.innerHTML = `<p>${escapeHtml(content)}</p>`;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMessage(text) {
    // Basic formatting - preserve newlines and escape HTML
    return escapeHtml(text)
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// PDF Export function
function exportChatToPDF() {
    const messages = document.querySelectorAll('.message');
    
    if (messages.length === 0) {
        addSystemMessage('No messages to export');
        return;
    }

    // Create a container for the PDF content
    const element = document.createElement('div');
    element.style.padding = '20px';
    element.style.fontFamily = 'Arial, sans-serif';
    element.style.lineHeight = '1.6';
    element.style.color = '#333';
    element.style.backgroundColor = '#fff';

    // Add title
    const title = document.createElement('h1');
    title.textContent = `Chat Export - ${currentSession?.name || 'Session'}`;
    title.style.marginBottom = '10px';
    title.style.borderBottom = '2px solid #3b82f6';
    title.style.paddingBottom = '10px';
    element.appendChild(title);

    // Add timestamp
    const timestamp = document.createElement('p');
    timestamp.textContent = `Exported on: ${new Date().toLocaleString()}`;
    timestamp.style.color = '#666';
    timestamp.style.marginBottom = '20px';
    element.appendChild(timestamp);

    // Add messages
    messages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.style.marginBottom = '15px';
        msgDiv.style.padding = '10px';
        msgDiv.style.borderRadius = '8px';

        const messageContent = msg.querySelector('p');
        const text = messageContent ? messageContent.textContent : '';

        if (msg.classList.contains('user')) {
            msgDiv.style.backgroundColor = '#e3f2fd';
            msgDiv.style.borderLeft = '4px solid #3b82f6';
            msgDiv.innerHTML = `<strong>You:</strong> ${text}`;
        } else if (msg.classList.contains('assistant')) {
            msgDiv.style.backgroundColor = '#f5f5f5';
            msgDiv.style.borderLeft = '4px solid #64748b';
            msgDiv.innerHTML = `<strong>Assistant:</strong> ${text}`;
        } else if (msg.classList.contains('system')) {
            msgDiv.style.backgroundColor = '#f0f0f0';
            msgDiv.style.color = '#666';
            msgDiv.style.fontStyle = 'italic';
            msgDiv.innerHTML = `<em>${text}</em>`;
        }

        element.appendChild(msgDiv);
    });

    // Generate PDF
    const opt = {
        margin: 10,
        filename: `StudyRAG_${currentSession?.name || 'chat'}_${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };

    html2pdf().set(opt).from(element).save();
    addSystemMessage('✓ Chat exported to PDF');
}
