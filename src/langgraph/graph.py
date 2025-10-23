"""
Updated Graph with Multi-Tool Execution Support
"""
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from src.langgraph.nodes.decider import decide_tool
from src.langgraph.nodes.aggregator import aggregate_response
from src.tools.rag.rag_agent import rag_agent
from src.tools.research.research_agent import research_agent
from src.tools.websearch.websearch_tool import websearch_tool


class MyState(TypedDict):
    query: str
    tool: str
    results: list
    metadata: dict
    final_answer: str


def route_after_decider(state):
    """Route based on tool decision"""
    tool = state["tool"]

    if tool == "multi":
        return "multi_executor"
    else:
        return tool


def multi_executor(state):
    """
    Execute multiple tools and combine results
    """
    tools_to_run = state["metadata"].get("tools", [])
    queries = state["metadata"].get("queries", {})

    print(f"\n{'=' * 60}")
    print(f"🔀 MULTI-EXECUTOR: Running {len(tools_to_run)} tools")
    print(f"{'=' * 60}")

    all_results = []

    for tool_name in tools_to_run:
        print(f"\n▶️  Executing: {tool_name.upper()}")

        # Get tool-specific query or use original
        tool_query = queries.get(tool_name, state["query"])
        print(f"   Query: '{tool_query}'")

        # Create temporary state for this tool
        temp_state = {
            "query": tool_query,
            "tool": tool_name,
            "results": [],
            "metadata": {},
            "final_answer": ""
        }

        # Execute the appropriate tool
        try:
            if tool_name == "rag":
                result = rag_agent(temp_state)
            elif tool_name == "research":
                result = research_agent(temp_state)
            elif tool_name == "websearch":
                result = websearch_tool(temp_state)
            else:
                print(f"   ⚠️  Unknown tool: {tool_name}")
                continue

            # Get results from this tool
            tool_results = result.get("results", [])

            if tool_results:
                # Add section header
                header = f"\n{'=' * 60}\n📋 {tool_name.upper()} RESULTS\n{'=' * 60}\n"
                all_results.append(header)

                # Add the actual results
                all_results.extend(tool_results)

                print(f"   ✅ Got {len(tool_results)} results")
            else:
                print(f"   ⚠️  No results from {tool_name}")

        except Exception as e:
            print(f"   ❌ Error executing {tool_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"✅ MULTI-EXECUTOR: Combined {len(all_results)} total results")
    print(f"{'=' * 60}\n")

    # Return combined results
    return {
        **state,
        "results": all_results,
        "tool": "multi"  # Mark as multi for aggregator
    }


def build_graph():
    """Build the LangGraph workflow"""

    # Initialize graph
    graph = StateGraph(MyState)

    # Add all nodes
    graph.add_node("decider", decide_tool)
    graph.add_node("rag", rag_agent)
    graph.add_node("research", research_agent)
    graph.add_node("websearch", websearch_tool)
    graph.add_node("multi_executor", multi_executor)
    graph.add_node("aggregator", aggregate_response)

    # Set entry point
    graph.set_entry_point("decider")

    # Conditional routing from decider
    graph.add_conditional_edges(
        "decider",
        route_after_decider,
        {
            "rag": "rag",
            "research": "research",
            "websearch": "websearch",
            "multi_executor": "multi_executor"
        }
    )

    # All tool nodes go to aggregator
    graph.add_edge("rag", "aggregator")
    graph.add_edge("research", "aggregator")
    graph.add_edge("websearch", "aggregator")
    graph.add_edge("multi_executor", "aggregator")

    # Aggregator goes to END
    graph.add_edge("aggregator", END)

    # Compile and return
    compiled = graph.compile()
    print("✅ Graph compiled successfully with multi-tool support\n")

    return compiled