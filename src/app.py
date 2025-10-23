from src.langgraph.graph import build_graph
from dotenv import load_dotenv

load_dotenv()


def main():
    query = input("🩺 Ask your Medical AI Assistant: ")

    # Build and compile the graph
    graph = build_graph()

    # Initialize state with all required fields INCLUDING final_answer
    state = {
        "query": query,
        "tool": "",
        "results": [],
        "metadata": {},
        "final_answer": ""  # Initialize empty
    }

    # Run the graph
    result = graph.invoke(state)

    # Display the final answer
    final_answer = result.get("final_answer", "No response generated")

    print("\n💬 Final Answer:\n")
    print(final_answer)


if __name__ == "__main__":
    main()