"""Chat/conversation logic using LangChain with Ollama and RAG."""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict, Optional
import json
import os
from app.config import settings
from app.rag.retriever import VectorStore
from app.rag.embedder import generate_embedding
from app.rag.prompts import get_prompt_by_mode


class ChatBot:
    """LangChain-based chatbot using Ollama for local inference with RAG support."""

    def __init__(self, model: str = None, temperature: float = None, vector_store_path: str = None, history_path: str = None):
        """
        Initialize the chatbot with Ollama.

        Args:
            model: Ollama model to use (uses config default if None)
            temperature: Sampling temperature (uses config default if None)
            vector_store_path: Path to vector store for RAG (optional)
            history_path: Path to save chat history (optional)
        """
        if model is None:
            model = settings.OLLAMA_MODEL
        if temperature is None:
            temperature = settings.TEMPERATURE
            
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=settings.OLLAMA_BASE_URL,
        )
        self.messages: List = []
        self.system_prompt: str = get_prompt_by_mode('chat')
        self.current_mode: str = 'chat'
        
        # RAG support
        self.vector_store = None
        if vector_store_path:
            self.vector_store = VectorStore(vector_store_path)
        
        # History persistence
        self.history_path = history_path
        if history_path:
            self.load_history()

    def chat(self, user_input: str, use_rag: bool = True, mode: str = None) -> str:
        """
        Send a message and get a response.

        Args:
            user_input: User's message
            use_rag: Whether to use RAG for context retrieval
            mode: Prompt mode (chat, summary, points, flashcards, teacher, exam)

        Returns:
            AI response
        """
        # Update mode if specified
        if mode and mode != self.current_mode:
            self.set_mode(mode)
        
        # Retrieve relevant context if RAG is enabled
        context = ""
        retrieved_sources = []
        if use_rag and self.vector_store:
            context, retrieved_sources = self._retrieve_context(user_input)
        
        # Add user message to history
        self.messages.append(HumanMessage(content=user_input))
        
        # Prepare messages with system prompt and context
        system_message = self.system_prompt
        if context:
            system_message += f"\n\nRelevant context from documents:\n{context}"
        
        messages_to_send = [SystemMessage(content=system_message)] + self.messages
        
        # Get response from LLM
        response = self.llm.invoke(messages_to_send)
        
        # Add AI response to history
        self.messages.append(AIMessage(content=response.content))
        
        # Save history
        if self.history_path:
            self.save_history(retrieved_sources)
        
        return response.content
    
    def _retrieve_context(self, query: str, top_k: int = None) -> tuple[str, List[dict]]:
        """
        Retrieve relevant context from vector store.
        
        Args:
            query: User query
            top_k: Number of results (uses config default if None)
            
        Returns:
            Tuple of (formatted context string, list of source metadata)
        """
        if top_k is None:
            # Honor ALL_RESULTS config to retrieve the entire vector store
            top_k = None if settings.ALL_RESULTS else settings.TOP_K_RESULTS
            
        # Generate query embedding
        query_embedding = generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        if not results:
            return "", []
        
        # Format context
        context_parts = []
        sources = []
        for i, (metadata, score) in enumerate(results, 1):
            source = metadata.get('source', 'Unknown')
            page = metadata.get('page', '?')
            text = metadata.get('text', '')
            category = metadata.get('category', 'notes')
            
            context_parts.append(
                f"[{i}] Source: {source} (Page {page}, Category: {category})\n"
                f"Relevance: {score:.2f}\n"
                f"Content: {text}\n"
            )
            
            sources.append({
                'source': source,
                'page': page,
                'category': category,
                'relevance': float(score)
            })
        
        return "\n".join(context_parts), sources

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history."""
        history = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history

    def clear_history(self) -> None:
        """Clear conversation history and memory."""
        self.messages.clear()
        if self.history_path:
            self.save_history([])

    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Set a system prompt for the conversation.

        Args:
            system_prompt: System instructions for the AI
        """
        self.system_prompt = system_prompt
    
    def set_mode(self, mode: str) -> None:
        """
        Set the conversation mode with appropriate prompt template.
        
        Args:
            mode: Mode name (chat, summary, points, flashcards, teacher, exam)
        """
        self.current_mode = mode
        self.system_prompt = get_prompt_by_mode(mode)
        print(f"Mode switched to: {mode}")
    
    def save_history(self, sources: List[dict] = None):
        """
        Save conversation history to file.
        
        Args:
            sources: Retrieved sources for the last response
        """
        if not self.history_path:
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        
        # Prepare history data
        history_data = {
            'messages': self.get_conversation_history(),
            'last_sources': sources or []
        }
        
        # Save to file
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    
    def load_history(self):
        """Load conversation history from file."""
        if not self.history_path or not os.path.exists(self.history_path):
            return
        
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # Restore messages
            self.messages.clear()
            for msg in history_data.get('messages', []):
                if msg['role'] == 'user':
                    self.messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    self.messages.append(AIMessage(content=msg['content']))
        except Exception as e:
            print(f"Error loading history: {e}")


def main():
    """Main function to run the chat application."""
    bot = ChatBot()

    # Set a system prompt
    bot.set_system_prompt(
        "You are a helpful AI assistant. Provide clear and concise answers."
    )

    print("StudyRAG Chat - Type 'exit' to quit")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if not user_input:
                continue

            response = bot.chat(user_input)
            print(f"\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\nChat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()