/**
 * API client for StudyRAG backend
 */

// Determine API base URL with sensible fallbacks
const API_BASE = (() => {
    // Query param override (?api_base=http://localhost:8000)
    if (typeof window !== 'undefined') {
        const urlBase = new URLSearchParams(window.location.search).get('api_base');
        if (urlBase) {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('studyrag_api_base', urlBase);
            }
            return urlBase;
        }
    }

    // Allow override via global or localStorage for flexibility
    const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('studyrag_api_base') : null;
    const globalVal = typeof window !== 'undefined' ? window.STUDYRAG_API_BASE : null;
    if (stored) return stored;
    if (globalVal) return globalVal;

    // If running from a file:// origin, default to localhost
    const isFile = typeof window !== 'undefined' && window.location.protocol === 'file:';
    if (isFile) return 'http://localhost:8000';

    // When served by nginx (port 80), use relative URLs so nginx can proxy
    const { protocol, hostname, port } = window.location;
    if (port === '80' || port === '') {
        return '';  // Use relative URLs, nginx will proxy
    }

    // Otherwise, use same host with backend port 8000
    return `${protocol}//${hostname || 'localhost'}:8000`;
})();

class StudyRAGAPI {
    /**
     * Get all sessions
     */
    static async getSessions() {
        try {
            const response = await fetch(`${API_BASE}/api/sessions`);
            if (!response.ok) {
                const text = await response.text().catch(() => '');
                throw new Error(`Failed to fetch sessions (status ${response.status}): ${text || response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting sessions:', error);
            throw error;
        }
    }

    /**
     * Get a specific session
     */
    static async getSession(sessionId) {
        try {
            const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
            if (!response.ok) throw new Error('Session not found');
            return await response.json();
        } catch (error) {
            console.error('Error getting session:', error);
            throw error;
        }
    }

    /**
     * Get uploads for a session
     */
    static async getSessionFiles(sessionId) {
        try {
            const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/files`);
            if (!response.ok) throw new Error('Files not found');
            return await response.json();
        } catch (error) {
            console.error('Error getting files:', error);
            return [];
        }
    }

    /**
     * Create a new session
     */
    static async createSession(name, category = 'notes') {
        try {
            const response = await fetch(`${API_BASE}/api/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    category_map: category,
                })
            });
            if (!response.ok) throw new Error('Failed to create session');
            return await response.json();
        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }

    /**
     * Delete a session
     */
    static async deleteSession(sessionId) {
        try {
            const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
                method: 'DELETE',
            });
            if (!response.ok) throw new Error('Failed to delete session');
            return await response.json();
        } catch (error) {
            console.error('Error deleting session:', error);
            throw error;
        }
    }

    /**
     * Upload a document
     */
    static async uploadDocument(sessionId, file, category = 'notes') {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', sessionId);
            formData.append('category', category);

            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) throw new Error('Failed to upload document');
            return await response.json();
        } catch (error) {
            console.error('Error uploading document:', error);
            throw error;
        }
    }

    /**
     * Send a chat message
     */
    static async chat(sessionId, message, mode = 'chat') {
        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: message,
                    mode: mode,
                })
            });
            if (!response.ok) throw new Error('Failed to send message');
            return await response.json();
        } catch (error) {
            console.error('Error sending chat message:', error);
            throw error;
        }
    }

    /**
     * Quick action - Explain simple
     */
    static async explainSimple(sessionId, topic = null) {
        try {
            const response = await fetch(`${API_BASE}/explain-simple`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    topic: topic,
                })
            });
            if (!response.ok) throw new Error('Failed to get explanation');
            return await response.json();
        } catch (error) {
            console.error('Error getting explanation:', error);
            throw error;
        }
    }

    /**
     * Quick action - Important points
     */
    static async importantPoints(sessionId, topic = null) {
        try {
            const response = await fetch(`${API_BASE}/important-points`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    topic: topic,
                })
            });
            if (!response.ok) throw new Error('Failed to get points');
            return await response.json();
        } catch (error) {
            console.error('Error getting points:', error);
            throw error;
        }
    }

    /**
     * Quick action - Revise fast (summary)
     */
    static async reviseFast(sessionId, topic = null) {
        try {
            const response = await fetch(`${API_BASE}/revise-fast`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    topic: topic,
                })
            });
            if (!response.ok) throw new Error('Failed to get summary');
            return await response.json();
        } catch (error) {
            console.error('Error getting summary:', error);
            throw error;
        }
    }

    /**
     * Quick action - Ask questions (exam)
     */
    static async askQuestions(sessionId, topic = null) {
        try {
            const response = await fetch(`${API_BASE}/ask-questions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    topic: topic,
                })
            });
            if (!response.ok) throw new Error('Failed to generate questions');
            return await response.json();
        } catch (error) {
            console.error('Error generating questions:', error);
            throw error;
        }
    }

    /**
     * Get chat history for a session
     */
    static async getChatHistory(sessionId) {
        try {
            const response = await fetch(`${API_BASE}/sessions/${sessionId}/history`);
            if (!response.ok) throw new Error('Failed to fetch chat history');
            return await response.json();
        } catch (error) {
            console.error('Error getting chat history:', error);
            return { messages: [] };
        }
    }

    /**
     * Health check
     */
    static async health() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (!response.ok) throw new Error('Health check failed');
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            throw error;
        }
    }
}

// Expose base for diagnostics
StudyRAGAPI.API_BASE = API_BASE;
