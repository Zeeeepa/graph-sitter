import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.graph import CompiledGraph
from langsmith import Client

# Import Codegen SDK if available
try:
    from codegen import Agent as CodegenAgent
    CODEGEN_AVAILABLE = True
except ImportError:
    CODEGEN_AVAILABLE = False

from contexten.agents.loggers import ExternalLogger
from contexten.agents.tracer import MessageStreamTracer
from contexten.agents.langchain.agent import create_codebase_agent
from contexten.agents.langchain.utils.get_langsmith_url import (
    find_and_print_langsmith_run_url,
)

if TYPE_CHECKING:
    from graph_sitter import Codebase

from contexten.agents.utils import AgentConfig


class CodeAgent:
    """Agent for interacting with a codebase with optional Codegen SDK integration."""

    codebase: "Codebase"
    agent: CompiledGraph
    langsmith_client: Client
    project_name: str
    thread_id: str | None = None
    run_id: str | None = None
    instance_id: str | None = None
    difficulty: int | None = None
    logger: Optional[ExternalLogger] = None
    use_codegen_sdk: bool = False
    codegen_agent: Optional[CodegenAgent] = None

    def __init__(
        self,
        codebase: "Codebase",
        model_provider: str = "anthropic",
        model_name: str = "claude-3-7-sonnet-latest",
        memory: bool = True,
        tools: Optional[list[BaseTool]] = None,
        tags: Optional[list[str]] = [],
        metadata: Optional[dict] = {},
        agent_config: Optional[AgentConfig] = None,
        thread_id: Optional[str] = None,
        logger: Optional[ExternalLogger] = None,
        use_codegen_sdk: Optional[bool] = None,
        **kwargs,
    ):
        """Initialize a CodeAgent.

        Args:
            codebase: The codebase to operate on
            model_provider: The model provider to use ("anthropic" or "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            tools: Additional tools to use
            tags: Tags to add to the agent trace. Must be of the same type.
            metadata: Metadata to use for the agent. Must be a dictionary.
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
                print(f"✅ CodeAgent initialized with Codegen SDK (org_id: {org_id})")
            else:
                print("⚠️ Codegen SDK requested but missing CODEGEN_ORG_ID or CODEGEN_TOKEN")
                self.codegen_agent = None
                self.use_codegen_sdk = False
        else:
            self.codegen_agent = None
        
        # Initialize local LangChain agent as fallback or primary
        self.agent = create_codebase_agent(
            self.codebase,
            model_provider=model_provider,
            model_name=model_name,
            memory=memory,
            additional_tools=tools,
            config=agent_config,
            **kwargs,
        )
        self.model_name = model_name
        self.langsmith_client = Client()

        if thread_id is None:
            self.thread_id = str(uuid4())
        else:
            self.thread_id = thread_id

        # Get project name from environment variable or use a default
        self.project_name = os.environ.get("LANGCHAIN_PROJECT", "RELACE")
        print(f"Using LangSmith project: {self.project_name}")

        # Store SWEBench metadata if provided
        metadata = metadata or {}
        self.run_id = metadata.get("run_id")
        self.instance_id = metadata.get("instance_id")
        # Extract difficulty value from "difficulty_X" format
        difficulty_str = metadata.get("difficulty", "")
        self.difficulty = int(difficulty_str.split("_")[1]) if difficulty_str and "_" in difficulty_str else None

        # Initialize tags for agent trace
        self.tags = list(tags) + [self.model_name]

        # set logger if provided
        self.logger = logger

        # Initialize metadata for agent trace
        self.metadata = {
            "project": self.project_name,
            "model": self.model_name,
            **metadata,
        }

    def _should_use_codegen_sdk(self) -> bool:
        """Check if Codegen SDK should be used based on environment variables."""
        return (
            CODEGEN_AVAILABLE and 
            os.getenv("CODEGEN_ORG_ID") is not None and 
            os.getenv("CODEGEN_TOKEN") is not None
        )

    def run(self, prompt: str, image_urls: Optional[list[str]] = None) -> str:
        """Run the agent with a prompt and optional images.

        Args:
            prompt: The prompt to run
            image_urls: Optional list of base64-encoded image strings. Example: ["data:image/png;base64,<base64_str>"]

        Returns:
            The agent's response
        """
        # Try Codegen SDK first if available
        if self.use_codegen_sdk and self.codegen_agent:
            try:
                print(f"🤖 Using Codegen SDK for prompt: {prompt[:100]}...")
                
                # For code tasks, we can enhance the prompt with codebase context
                enhanced_prompt = f"""
Codebase Context: {self.codebase.repo_path}

Task: {prompt}

Please analyze the codebase and implement the requested changes.
"""
                
                task = self.codegen_agent.run(prompt=enhanced_prompt)
                
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
        
        self.config = {
            "configurable": {
                "thread_id": self.thread_id,
                "metadata": {"project": self.project_name},
            },
            "recursion_limit": 100,
        }

        # Prepare content with prompt and images if provided
        content = [{"type": "text", "text": prompt}]
        if image_urls:
            content += [{"type": "image_url", "image_url": {"url": image_url}} for image_url in image_urls]

        config = RunnableConfig(configurable={"thread_id": self.thread_id}, tags=self.tags, metadata=self.metadata, recursion_limit=200)
        # we stream the steps instead of invoke because it allows us to access intermediate nodes

        stream = self.agent.stream({"messages": [HumanMessage(content=content)]}, config=config, stream_mode="values")

        _tracer = MessageStreamTracer(logger=self.logger)

        # Process the stream with the tracer
        traced_stream = _tracer.process_stream(stream)

        # Keep track of run IDs from the stream
        run_ids = []

        for s in traced_stream:
            if len(s["messages"]) == 0 or isinstance(s["messages"][-1], HumanMessage):
                message = HumanMessage(content=content)
            else:
                message = s["messages"][-1]

            if isinstance(message, tuple):
                # print(message)
                pass
            else:
                if isinstance(message, AIMessage) and isinstance(message.content, list) and len(message.content) > 0 and "text" in message.content[0]:
                    AIMessage(message.content[0]["text"]).pretty_print()
                else:
                    message.pretty_print()

                # Try to extract run ID if available in metadata
                if hasattr(message, "additional_kwargs") and "run_id" in message.additional_kwargs:
                    run_ids.append(message.additional_kwargs["run_id"])

        # Get the last message content
        result = s["final_answer"]

        # # Try to find run IDs in the LangSmith client's recent runs
        try:
            # Find and print the LangSmith run URL
            find_and_print_langsmith_run_url(self.langsmith_client, self.project_name)
        except Exception as e:
            separator = "=" * 60
            print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
            import traceback

            print(traceback.format_exc())
            print(separator)

        return result

    def get_agent_trace_url(self) -> str | None:
        """Get the URL for the most recent agent run in LangSmith.

        Returns:
            The URL for the run in LangSmith if found, None otherwise
        """
        try:
            # TODO - this is definitely not correct, we should be able to get the URL directly...
            return find_and_print_langsmith_run_url(client=self.langsmith_client, project_name=self.project_name)
        except Exception as e:
            separator = "=" * 60
            print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
            import traceback

            print(traceback.format_exc())
            print(separator)
            return None

    def get_tools(self) -> list[BaseTool]:
        return list(self.agent.get_graph().nodes["tools"].data.tools_by_name.values())

    def get_state(self) -> dict:
        return self.agent.get_state(self.config)

    def get_tags_metadata(self) -> tuple[list[str], dict]:
        tags = [self.model_name]
        metadata = {"project": self.project_name, "model": self.model_name}
        # Add SWEBench run ID and instance ID to the metadata and tags for filtering
        if self.run_id is not None:
            metadata["swebench_run_id"] = self.run_id
            tags.append(self.run_id)

        if self.instance_id is not None:
            metadata["swebench_instance_id"] = self.instance_id
            tags.append(self.instance_id)

        if self.difficulty is not None:
            metadata["swebench_difficulty"] = self.difficulty
            tags.append(f"difficulty_{self.difficulty}")

        return tags, metadata
