import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage

from contexten.agents.langchain.agent import create_chat_agent

# Import Codegen SDK if available
try:
    from codegen import Agent as CodegenAgent
    CODEGEN_AVAILABLE = True
except ImportError:
    CODEGEN_AVAILABLE = False

if TYPE_CHECKING:
    from graph_sitter import Codebase


class ChatAgent:
    """Agent for interacting with a codebase with optional Codegen SDK integration."""

    def __init__(self, codebase: "Codebase", model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", memory: bool = True, tools: Optional[list[BaseTool]] = None, use_codegen_sdk: bool = None, **kwargs):
        """Initialize a ChatAgent.

        Args:
            codebase: The codebase to operate on
            model_provider: The model provider to use ("anthropic" or "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            tools: Additional tools to use
            use_codegen_sdk: Whether to use Codegen SDK. If None, auto-detect from environment
            **kwargs: Additional LLM configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
        """
        self.codebase = codebase
        
        # Check if Codegen SDK should be used
        if use_codegen_sdk is None:
            use_codegen_sdk = self._should_use_codegen_sdk()
        
        self.use_codegen_sdk = use_codegen_sdk
        
        if self.use_codegen_sdk and CODEGEN_AVAILABLE:
            # Initialize Codegen SDK agent
            org_id = os.getenv("CODEGEN_ORG_ID")
            token = os.getenv("CODEGEN_TOKEN")
            
            if org_id and token:
                self.codegen_agent = CodegenAgent(org_id=org_id, token=token)
                print(f"✅ ChatAgent initialized with Codegen SDK (org_id: {org_id})")
            else:
                print("⚠️ Codegen SDK requested but missing CODEGEN_ORG_ID or CODEGEN_TOKEN")
                self.codegen_agent = None
                self.use_codegen_sdk = False
        else:
            self.codegen_agent = None
        
        # Initialize local LangChain agent as fallback or primary
        self.agent = create_chat_agent(self.codebase, model_provider=model_provider, model_name=model_name, memory=memory, additional_tools=tools, **kwargs)

    def _should_use_codegen_sdk(self) -> bool:
        """Check if Codegen SDK should be used based on environment variables."""
        return (
            CODEGEN_AVAILABLE and 
            os.getenv("CODEGEN_ORG_ID") is not None and 
            os.getenv("CODEGEN_TOKEN") is not None
        )

    def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            The agent's response
        """
        if thread_id is None:
            thread_id = str(uuid4())

        # Try Codegen SDK first if available
        if self.use_codegen_sdk and self.codegen_agent:
            try:
                print(f"🤖 Using Codegen SDK for prompt: {prompt[:100]}...")
                task = self.codegen_agent.run(prompt=prompt)
                
                # Wait for completion and return result
                while task.status not in ["completed", "failed", "cancelled"]:
                    task.refresh()
                
                if task.status == "completed":
                    return task.result
                else:
                    print(f"⚠️ Codegen SDK task failed with status: {task.status}")
                    # Fall back to local agent
            except Exception as e:
                print(f"⚠️ Codegen SDK error: {e}, falling back to local agent")

        # Use local LangChain agent
        print(f"🔧 Using local LangChain agent for prompt: {prompt[:100]}...")
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
        # Access the agent's memory to get conversation history
        if hasattr(self.agent, "get_state"):
            state = self.agent.get_state({"configurable": {"thread_id": thread_id}})
            if state and "messages" in state:
                return state["messages"]
        return []
