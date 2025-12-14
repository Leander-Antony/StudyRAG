"""Database connection and setup using SQLite."""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager
import os
from app.config import settings


class Database:
    """SQLite database manager for StudyRAG sessions."""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (uses config default if None)
        """
        if db_path is None:
            db_path = settings.DATABASE_PATH
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _migrate_add_last_used(self):
        """Add last_used column to existing sessions table if not present."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists
                pass
            except Exception as e:
                print(f"last_used migration error: {e}")

    def _ensure_uploads_table(self):
        """Create uploads table if missing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    upload_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    category TEXT DEFAULT 'notes',
                    chunks_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()

    def init_db(self):
        """Initialize database and create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category_map TEXT DEFAULT 'notes',
                    vector_index_path TEXT,
                    chat_history_path TEXT
                )
            """)
            conn.commit()
        
        # Add last_used column if it doesn't exist (migration)
        self._migrate_add_last_used()
        self._ensure_uploads_table()

    def create_session(
        self,
        session_id: str,
        name: str,
        category_map: str = "notes",
        vector_index_path: Optional[str] = None,
        chat_history_path: Optional[str] = None,
    ) -> Dict:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            name: Session name (subject/workspace)
            category_map: Category type (notes/qpapers)
            vector_index_path: Path to vector index
            chat_history_path: Path to chat history

        Returns:
            Created session as dictionary
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (session_id, name, category_map, vector_index_path, chat_history_path)
                VALUES (?, ?, ?, ?, ?)
            """,
                (session_id, name, category_map, vector_index_path, chat_history_path),
            )
            conn.commit()

        return self.get_session(session_id)

    def add_upload(
        self,
        upload_id: str,
        session_id: str,
        filename: str,
        category: str = "notes",
        chunks_count: int = 0,
    ) -> Dict:
        """Record an uploaded file for a session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO uploads (upload_id, session_id, filename, category, chunks_count)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (upload_id, session_id, filename, category, chunks_count),
                )
                conn.commit()
            return self.get_upload(upload_id)
        except sqlite3.OperationalError as e:
            if "no such table: uploads" in str(e):
                self._ensure_uploads_table()
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO uploads (upload_id, session_id, filename, category, chunks_count)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (upload_id, session_id, filename, category, chunks_count),
                    )
                    conn.commit()
                return self.get_upload(upload_id)
            raise

    def get_upload(self, upload_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uploads WHERE upload_id = ?", (upload_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_uploads_for_session(self, session_id: str) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM uploads WHERE session_id = ? ORDER BY created_at DESC",
                    (session_id,),
                )
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            if "no such table: uploads" in str(e):
                self._ensure_uploads_table()
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT * FROM uploads WHERE session_id = ? ORDER BY created_at DESC",
                        (session_id,),
                    )
                    rows = cursor.fetchall()
                    return [dict(r) for r in rows]
            raise

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_all_sessions(self) -> List[Dict]:
        """
        Get all sessions.

        Returns:
            List of session dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions ORDER BY last_used DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.OperationalError as e:
            # Handle legacy DBs missing last_used column
            if "no such column: last_used" in str(e):
                self._migrate_add_last_used()
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            raise
    
    def update_last_used(self, session_id: str) -> Optional[Dict]:
        """
        Update the last_used timestamp for a session.

        Args:
            session_id: Session identifier

        Returns:
            Updated session or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET last_used = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
        
        return self.get_session(session_id)

    def update_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        category_map: Optional[str] = None,
        vector_index_path: Optional[str] = None,
        chat_history_path: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Update session fields.

        Args:
            session_id: Session identifier
            name: New session name
            category_map: New category
            vector_index_path: New vector index path
            chat_history_path: New chat history path

        Returns:
            Updated session or None
        """
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if category_map is not None:
            updates.append("category_map = ?")
            params.append(category_map)
        if vector_index_path is not None:
            updates.append("vector_index_path = ?")
            params.append(vector_index_path)
        if chat_history_path is not None:
            updates.append("chat_history_path = ?")
            params.append(chat_history_path)

        if not updates:
            return self.get_session(session_id)

        params.append(session_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?",
                params,
            )
            conn.commit()

        return self.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated files.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False otherwise
        """
        # Get session info before deleting
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Delete associated files
        self._cleanup_session_files(session)
        
        # Delete from database
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def _cleanup_session_files(self, session: dict):
        """
        Clean up all files associated with a session.
        
        Args:
            session: Session dictionary with file paths
        """
        import os
        
        # Delete vector index files
        vector_path = session.get('vector_index_path')
        if vector_path:
            # FAISS creates .index and .meta files
            index_file = f"{vector_path}.index"
            meta_file = f"{vector_path}.meta"
            
            if os.path.exists(index_file):
                os.remove(index_file)
                print(f"Deleted vector index: {index_file}")
            
            if os.path.exists(meta_file):
                os.remove(meta_file)
                print(f"Deleted vector metadata: {meta_file}")
        
        # Delete chat history file
        history_path = session.get('chat_history_path')
        if history_path and os.path.exists(history_path):
            os.remove(history_path)
            print(f"Deleted chat history: {history_path}")

    def get_sessions_by_category(self, category_map: str) -> List[Dict]:
        """
        Get all sessions by category.

        Args:
            category_map: Category to filter by (notes/qpapers)

        Returns:
            List of session dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM sessions WHERE category_map = ? ORDER BY last_used DESC",
                    (category_map,),
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.OperationalError as e:
            if "no such column: last_used" in str(e):
                self._migrate_add_last_used()
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT * FROM sessions WHERE category_map = ? ORDER BY created_at DESC",
                        (category_map,),
                    )
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            raise


# Global database instance
db = Database()
