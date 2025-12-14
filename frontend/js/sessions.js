/**
 * Sessions page - List and manage study sessions
 */

// DOM Elements
const createSessionBtn = document.getElementById('createSessionBtn');
const createSessionModal = document.getElementById('createSessionModal');
const createSessionForm = document.getElementById('createSessionForm');
const sessionsList = document.getElementById('sessionsList');
const modalClose = document.querySelector('.modal-close');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
    loadSessions();
});

async function checkHealth() {
    try {
        const health = await StudyRAGAPI.health();
    } catch (err) {
        if (infoEl) infoEl.textContent = `API: ${StudyRAGAPI.API_BASE} ✗ health failed`;
        console.error('Health check failed', err);
    }
}

function setupEventListeners() {
    createSessionBtn.addEventListener('click', openCreateModal);
    modalClose.addEventListener('click', closeCreateModal);
    createSessionForm.addEventListener('submit', handleCreateSession);

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === createSessionModal) {
            closeCreateModal();
        }
    });
}

async function loadSessions() {
    try {
        sessionsList.innerHTML = '<p class="loading">Loading sessions...</p>';
        const sessions = await StudyRAGAPI.getSessions();

        if (sessions.length === 0) {
            sessionsList.innerHTML = '<p class="loading">No sessions yet. Create one to get started!</p>';
            return;
        }

        sessionsList.innerHTML = '';
        sessions.forEach(session => {
            const card = createSessionCard(session);
            sessionsList.appendChild(card);
        });
    } catch (error) {
        sessionsList.innerHTML = `<p class="loading" style="color: #ef4444;">Error loading sessions: ${error.message}<br>API: ${StudyRAGAPI ? StudyRAGAPI.API_BASE || 'http://localhost:8000' : 'http://localhost:8000'}</p>`;
        console.error('Sessions load failed', error);
    }
}

function createSessionCard(session) {
    const card = document.createElement('div');
    card.className = 'session-card';
    
    const createdDate = new Date(session.created_at).toLocaleDateString();
    const lastUsedDate = session.last_used ? new Date(session.last_used).toLocaleString() : 'Never';
    const categoryLabel = session.category_map === 'notes' ? 'Study Notes' : 'Question Papers';

    card.innerHTML = `
        <h3>${escapeHtml(session.name)}</h3>
        <div class="session-meta">
            <span class="badge">${categoryLabel}</span>
            <span title="Created: ${createdDate}">Last used: ${lastUsedDate}</span>
        </div>
        <div class="session-actions">
            <a href="chat.html?session_id=${session.session_id}" class="btn btn-primary btn-small">Open</a>
            <button class="btn btn-secondary btn-small" onclick="deleteSession('${session.session_id}', '${escapeHtml(session.name)}')">Delete</button>
        </div>
    `;

    return card;
}

function openCreateModal() {
    createSessionModal.classList.add('open');
    document.getElementById('sessionName').focus();
}

function closeCreateModal() {
    createSessionModal.classList.remove('open');
    createSessionForm.reset();
}

async function handleCreateSession(e) {
    e.preventDefault();

    const name = document.getElementById('sessionName').value.trim();
    const category = document.getElementById('sessionCategory').value;

    if (!name) {
        alert('Please enter a session name');
        return;
    }

    try {
        createSessionBtn.disabled = true;
        const response = await StudyRAGAPI.createSession(name, category);
        
        console.log('Session created:', response);
        closeCreateModal();
        
        // Reload sessions and navigate to chat
        await loadSessions();
        
        // Navigate to the chat screen
        window.location.href = `chat.html?session_id=${response.session_id}`;
    } catch (error) {
        alert(`Error creating session: ${error.message}`);
    } finally {
        createSessionBtn.disabled = false;
    }
}

async function deleteSession(sessionId, sessionName) {
    if (!confirm(`Delete session "${sessionName}" and all associated data?`)) {
        return;
    }

    try {
        await StudyRAGAPI.deleteSession(sessionId);
        console.log('Session deleted:', sessionId);
        await loadSessions();
    } catch (error) {
        alert(`Error deleting session: ${error.message}`);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
