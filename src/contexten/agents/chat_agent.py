from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage

# Updated import path after folder move
from contexten.agents.langchain.agent import create_chat_agent


from graph_sitter import Codebase


class ChatAgent:
    """Agent for interacting with a codebase."""

    def __init__(self, codebase: "Codebase", model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", memory: bool = True, tools: Optional[list[BaseTool]] = None, org_id: Optional[str] = None, token: Optional[str] = None, **kwargs):
        """Initialize a ChatAgent.

        Args:
            codebase: The codebase to operate on
            model_provider: The model provider to use ("anthropic" or "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            tools: Additional tools to use
            org_id: Optional Codegen organization ID (if provided, uses Codegen SDK)
            token: Optional Codegen API token (required if org_id is provided)
            **kwargs: Additional LLM configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
        """
        self.codebase = codebase
        self.use_codegen_sdk = org_id is not None and token is not None
        
        if self.use_codegen_sdk:
            # Use Codegen SDK
            from codegen import Agent
            self.codegen_agent = Agent(org_id=org_id, token=token)
            self.agent = None
        else:
            # Use existing langchain implementation
            self.agent = create_chat_agent(self.codebase, model_provider=model_provider, model_name=model_name, memory=memory, additional_tools=tools, **kwargs)
            self.codegen_agent = None

    def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            The agent's response
        """
        if self.use_codegen_sdk:
            # Use Codegen SDK
            task = self.codegen_agent.run(prompt=prompt)
            # Wait for task completion and return result
            while task.status not in ["completed", "failed", "cancelled"]:
                task.refresh()
                if task.status == "failed":
                    raise Exception(f"Codegen task failed: {task.error}")
            return task.result if task.result else "Task completed successfully"
        else:
            # Use existing langchain implementation
            if thread_id is None:
                thread_id = str(uuid4())

            input = {"query": prompt}
            stream = self.agent.stream(input, config={"configurable": {"thread_id": thread_id}}, stream_mode="values")

            for s in stream:
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    if isinstance(message, AIMessage) and isinstance(message.content, list) and "text" in message.content[0]:
                        AIMessage(message.content[0]["text"]).pretty_print()
                    else:
                        message.pretty_print()

            return s["final_answer"]

    def chat(self, prompt: str, thread_id: Optional[str] = None) -> tuple[str, str]:
        """Chat with the agent, maintaining conversation history.

        Args:
            prompt: The user message
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            A tuple of (response_content, thread_id) to allow continued conversation
        """
        if self.use_codegen_sdk:
            # For Codegen SDK, we don't have built-in thread support yet
            # So we'll just run the prompt and return a generated thread_id
            if thread_id is None:
                thread_id = str(uuid4())
                print(f"Starting new chat thread: {thread_id}")
            else:
                print(f"Continuing chat thread: {thread_id}")
            
            response = self.run(prompt, thread_id=thread_id)
            return response, thread_id
        else:
            # Use existing langchain implementation
            if thread_id is None:
                thread_id = str(uuid4())
                print(f"Starting new chat thread: {thread_id}")
            else:
                print(f"Continuing chat thread: {thread_id}")

            response = self.run(prompt, thread_id=thread_id)
            return response, thread_id

    def get_chat_history(self, thread_id: str) -> list:
        """Retrieve the chat history for a specific thread.

        Args:
            thread_id: The thread ID to retrieve history for

        Returns:
            List of messages in the conversation history
        """
        if self.use_codegen_sdk:
            # Codegen SDK doesn't have built-in chat history yet
            # Return empty list for now
            return []
        else:
            # Access the agent's memory to get conversation history
            if hasattr(self.agent, "get_state"):
                state = self.agent.get_state({"configurable": {"thread_id": thread_id}})
                if state and "messages" in state:
                    return state["messages"]
            return []

