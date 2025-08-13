import asyncio
import logging
from mcp_orchestrator import MCPOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_example")

async def main():
    """Main function to demonstrate the MCP orchestrator."""
    logger.info("Starting MCP orchestrator example...")
    
    try:
        # Create an orchestrator
        orchestrator = MCPOrchestrator()
        
        # Start a server
        await orchestrator.start_server("example-server", "python", ["test_mcp_server_fixed.py"])
        
        # Create a client
        orchestrator.create_client("example-client", "example-server")
        
        # Initialize the client
        logger.info("Initializing client...")
        try:
            # Set a timeout for the initialization
            async with asyncio.timeout(5):
                result = await orchestrator.initialize_client("example-client")
                logger.info(f"Initialization result: {result}")
                
                # List the tools
                logger.info("Listing tools...")
                tools = await orchestrator.list_tools("example-client")
                logger.info(f"Tools: {tools}")
                
                # Call the hello_world tool
                logger.info("Calling hello_world tool...")
                result = await orchestrator.call_tool("example-client", "hello_world")
                logger.info(f"Tool result: {result}")
        except asyncio.TimeoutError:
            logger.error("Operation timed out")
        except Exception as e:
            logger.error(f"Operation error: {e}")
            import traceback
            traceback.print_exc()
        
        # Stop all servers
        await orchestrator.stop_all_servers()
        
        logger.info("Example completed successfully.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("Example finished.")

if __name__ == "__main__":
    asyncio.run(main())

