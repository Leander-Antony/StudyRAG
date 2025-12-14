"""Chat/conversation logic using LangChain with Ollama."""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict


class ChatBot:
    """LangChain-based chatbot using Ollama for local inference."""

    def __init__(self, model: str = "llama3:latest", temperature: float = 0.7):
        """
        Initialize the chatbot with Ollama.

        Args:
            model: Ollama model to use (default: llama3:latest)
            temperature: Sampling temperature (0-1)
        """
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url="http://localhost:11434",
        )
        self.messages: List = []
        self.system_prompt: str = "You are a helpful AI assistant. Provide clear and concise answers."

    def chat(self, user_input: str) -> str:
        """
        Send a message and get a response.

        Args:
            user_input: User's message

        Returns:
            AI response
        """
        # Add user message to history
        self.messages.append(HumanMessage(content=user_input))
        
        # Prepare messages with system prompt
        messages_to_send = [SystemMessage(content=self.system_prompt)] + self.messages
        
        # Get response from LLM
        response = self.llm.invoke(messages_to_send)
        
        # Add AI response to history
        self.messages.append(AIMessage(content=response.content))
        
        return response.content

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

    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Set a system prompt for the conversation.

        Args:
            system_prompt: System instructions for the AI
        """
        self.system_prompt = system_prompt


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