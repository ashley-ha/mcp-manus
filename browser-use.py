from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Optional, Union
import asyncio

import json
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller
from browser_use.agent.views import ActionResult

import sys
import logging





# Configure a custom stderr handler for all logging
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(levelname)-8s [%(name)s] %(message)s"))

# Get the root logger and remove any existing handlers
root_logger = logging.getLogger()
root_logger.handlers = []
root_logger.addHandler(stderr_handler)
root_logger.setLevel(logging.INFO)

# Create our specific logger
logger = logging.getLogger("browser-agent")

# Force all loggers from third-party libraries to use stderr too
for third_party_logger_name in [
    "playwright", "httpx", "selenium", "asyncio", "browser_use", 
    "mcp", "langchain", "openai", "anthropic"
]:
    third_party_logger = logging.getLogger(third_party_logger_name)
    third_party_logger.handlers = []
    third_party_logger.addHandler(stderr_handler)
    third_party_logger.setLevel(logging.WARNING)  # Only show warnings and errors
    third_party_logger.propagate = False  # Don't propagate to root logger

# Configure the path to your google chrome browser (should be this but you can check with `which google chrome` in terminal)
CHROME_BROWSER = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

browser: Optional[Browser] = None
browser_context: Optional[BrowserContext] = None

@asynccontextmanager
async def browser_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage browser lifecycle"""
    global browser, browser_context
    browser = Browser(
        config=BrowserConfig(
            headless=False,  # This is True in production
            disable_security=True,
            chrome_instance_path=CHROME_BROWSER,
            new_context_config=BrowserContextConfig(
                disable_security=True,
                minimum_wait_page_load_time=1,  # 3 on prod
                maximum_wait_page_load_time=10,  # 20 on prod
                # no_viewport=True,
                browser_window_size={
                    'width': 1280,
                    'height': 1100,
                },
                save_recording_path='./tmp/recordings',
                # trace_path="./tmp/result_processing",
            ),
	    )
    )
    browser_context = await browser.new_context()
    controller = Controller()
    
    try:
        yield {
            "browser": browser,
            "browser_context": browser_context,
            "controller": controller
        }
    finally:
        await browser_context.close()
        await browser.close()

# Initialize FastMCP server
mcp = FastMCP("browser-agent", lifespan=browser_lifespan)

async def browser_initialized_check():
    """Ensure browser and context are initialized."""
    global browser, browser_context
    
    try:
        # Check if browser is actually responsive
        if browser is not None:
            try:
                await browser.is_connected()
            except Exception:
                logger.info("Browser not responsive, reinitializing...")
                browser = None
                browser_context = None
        
        if browser is None:
            logger.info("Initializing browser...")
            browser = Browser(
                config=BrowserConfig(
                    headless=False,
                    disable_security=True,
                    chrome_instance_path=CHROME_BROWSER,
                    new_context_config=BrowserContextConfig(
                        disable_security=True,
                        minimum_wait_page_load_time=1,
                        maximum_wait_page_load_time=10,
                        browser_window_size={
                            'width': 1280,
                            'height': 1100,
                        },
                        save_recording_path='./tmp/recordings',
                    ),
                )
            )
        
        if browser_context is None:
            logger.info("Creating new browser context...")
            browser_context = await browser.new_context()
            # Ensure we have at least one page open
            state = await browser_context.get_state()
            if not state.tabs:  # Check tabs from state instead of get_pages
                logger.info("Creating new page...")
                await browser_context.new_page()
    
        return browser_context
    except Exception as e:
        logger.error(f"Error initializing browser: {str(e)}")
        # Clean up if initialization failed
        if browser_context:
            await browser_context.close()
        if browser:
            await browser.close()
        browser = None
        browser_context = None
        raise

@mcp.tool()
async def get_planner_state(ctx: Context) -> str:
    """Get the current browser state and planning context.
    This tool must be executed before execute_actions tool.
    
    Must return a JSON string in the format:
    {
        "current_state": {
            "evaluation_previous_goal": "Success|Failed|Unknown - Analysis of previous actions",
            "memory": "Description of what has been done and what to remember",
            "next_goal": "What needs to be done with the next immediate action"
        },
        "action": [
            {"action_name": {"param1": "value1", ...}},
            ...
        ]
    }
    """
    try:
        browser_context = await browser_initialized_check()
        controller = ctx.request_context.lifespan_context.get("controller")
        
        if controller is None:
            controller = Controller()
            ctx.request_context.lifespan_context["controller"] = controller
        
        state = await browser_context.get_state()
        elements_text = state.element_tree.clickable_elements_to_string() # dom to html step -- basically gets elements on the page and returns for text representation input to llm
        
        # Get available actions from the controller's registry
        available_actions = controller.registry.get_prompt_description() # gets the action descriptions from the controller
        
        # Format the response according to system prompt
        response = {
            "current_state": {
                "evaluation_previous_goal": "Unknown - No previous actions to evaluate",
                "memory": "Starting new browser session",
                "next_goal": "Ready to execute browser actions"
            },
            "action": []  # Empty action list - actions will be specified by the caller
        }
        
        # Add browser state information
        state_info = f"""
            Current URL: {state.url}
            Title: {state.title}
            Available tabs: {[tab.model_dump() for tab in state.tabs]}
            Interactive elements:
            {elements_text}

            Available Actions:
            {available_actions}

            Note: Actions should be executed using the execute_actions tool with the following format:
            {{
                "name": "action_name",
                "params": {{
                    "param1": "value1",
                    ...
                }}
            }}
            """
        return json.dumps(response, indent=2) + "\n\nBrowser State:\n" + state_info
    except Exception as e:
        logger.error(f"Error getting planner state: {str(e)}")
        return f"Error getting planner state: {str(e)}"

@mcp.tool()
async def execute_actions(actions: Dict[str, Any], ctx: Context) -> str:
    """Execute actions from the planner state.
    
    Args:
        actions: A dictionary containing the planner state and actions in format:
                {
                    "current_state": {
                        "evaluation_previous_goal": str,
                        "memory": str,
                        "next_goal": str
                    },
                    "action": [
                        {"action_name": {"param1": "value1"}},
                        ...
                    ]
                }
                
    Note: If the page state changes (new elements appear) during action execution,
    the sequence will be interrupted and you'll need to get a new planner state.
    """
    browser_context = await browser_initialized_check()
    controller = ctx.request_context.lifespan_context["controller"]
    
    try:
        # Validate input format
        if not isinstance(actions, dict) or "action" not in actions:
            return "Error: Actions must be a dictionary containing 'action' list"
        
        action_list = actions["action"]
        if not action_list:
            return "No actions to execute"
        
        # Get initial state for DOM change detection
        initial_state = await browser_context.get_state()
        initial_path_hashes = set(e.hash.branch_path_hash for e in initial_state.selector_map.values())
        
        # Convert system prompt action format to action models
        action_models = []
        for action_dict in action_list:
            if not isinstance(action_dict, dict) or len(action_dict) != 1:
                return "Error: Each action must be a dictionary with exactly one key-value pair"
                
            action_name = list(action_dict.keys())[0]
            params = action_dict[action_name]
            
            # Create action model using the controller's registry
            action_model = controller.registry.create_action_model()(**{action_name: params})
            action_models.append(action_model)
        
        # Execute actions one by one to check for DOM changes
        results = []
        for i, action_model in enumerate(action_models):
            # Execute single action
            result = await controller.act(action_model, browser_context)
            results.append(result)
            
            # Check if this action requires element interaction
            requires_elements = any(param in str(action_model) for param in ["index", "xpath"])
            
            # If not the last action and next action might need elements, check for DOM changes
            if i < len(action_models) - 1:
                new_state = await browser_context.get_state()
                new_path_hashes = set(e.hash.branch_path_hash for e in new_state.selector_map.values())
                
                # If DOM changed and next action needs elements, break sequence
                if requires_elements and not new_path_hashes.issubset(initial_path_hashes):
                    msg = f"Page state changed after action {i + 1}/{len(action_models)}. Please get new planner state before continuing."
                    logger.info(msg)
                    results.append(ActionResult(extracted_content=msg, include_in_memory=True))
                    break
            
            # Stop if there was an error
            if result.error:
                break
        
        # Process results
        output = []
        for result in results:
            if result.extracted_content:
                output.append(result.extracted_content)
            elif result.error:
                output.append(f"Error: {result.error}")
            else:
                output.append("Action executed successfully")
                
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error executing actions: {str(e)}")
        return f"Error executing actions: {str(e)}"

# Start the server
if __name__ == "__main__":
    mcp.run(transport='stdio')