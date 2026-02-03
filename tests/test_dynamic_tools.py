"""
Test script to explore Langchain's dynamic tool injection capabilities
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from config.config import CFG

# Create test tools
@tool
def tool_a(query: str) -> str:
    """Tool A for testing"""
    return f"Tool A executed: {query}"

@tool
def tool_b(query: str) -> str:
    """Tool B for testing"""
    return f"Tool B executed: {query}"

@tool
def load_more_tools(task: str) -> str:
    """Dynamically load additional tools based on task"""
    return f"LOAD_TOOLS:tool_b"

# Test 1: Create agent with initial tools
print("=== Test 1: Initial Agent Creation ===")
model = ChatGoogleGenerativeAI(model=CFG.chat_model, api_key=CFG.api_key)
agent = create_agent(model, tools=[tool_a, load_more_tools])

print(f"Agent type: {type(agent)}")
print(f"Agent class: {agent.__class__.__name__}")

# Test 2: Check if agent has mutable tools attribute
print("\n=== Test 2: Agent Attributes ===")
attrs = [a for a in dir(agent) if not a.startswith('_') and not callable(getattr(agent, a))]
print(f"Non-callable attributes: {attrs}")

# Test 3: Check if we can access the graph structure
print("\n=== Test 3: Graph Structure ===")
if hasattr(agent, 'nodes'):
    print(f"Nodes: {agent.nodes}")
if hasattr(agent, 'get_graph'):
    print("Has get_graph method")
    
# Test 4: Check CompiledStateGraph methods
print("\n=== Test 4: CompiledStateGraph Methods ===")
methods = [m for m in dir(agent) if not m.startswith('_') and callable(getattr(agent, m))]
print(f"Available methods: {methods[:10]}")  # Show first 10

# Test 5: Try to access internal state
print("\n=== Test 5: Internal State ===")
if hasattr(agent, '__dict__'):
    print(f"Agent __dict__ keys: {list(agent.__dict__.keys())}")

print("\n=== Conclusion ===")
print("CompiledStateGraph is immutable - tools are baked into the graph at compile time")
print("Solution: Recreate agent when tools change, or use tool that signals reload")
