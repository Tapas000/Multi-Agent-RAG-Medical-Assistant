"""
Aggregator Node - Enhanced for Multi-Tool Support
"""
import os
from langchain_groq import ChatGroq


def aggregate_response(state):
    """
    Aggregates results and generates final response
    Handles both single-tool and multi-tool results
    """
    tool = state["tool"]
    results = state.get("results", [])
    query = state["query"]

    print(f"🔄 Aggregator: Processing {len(results)} results from '{tool}'")

    # Handle empty results
    if not results:
        return {
            **state,
            "final_answer": "I couldn't find relevant information. Please try rephrasing your query."
        }

    # ============================================
    # MULTI-TOOL AGGREGATION
    # ============================================
    if tool == "multi":
        print(f"🔀 Aggregator: Combining multi-tool results with LLM")

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3
        )

        # Combine all results into context
        combined_context = "\n\n".join(str(r) for r in results)

        prompt = f"""You are a medical AI assistant. The user asked: "{query}"

I've gathered information from multiple sources (medical knowledge base and research databases):

{combined_context}

Please provide a comprehensive, well-organized response that:

1. **Medical Information**: Explain the condition, symptoms, and general treatment options
2. **Research Insights**: Highlight key findings from recent studies (if available)
3. **Organization**: Use clear headers and bullet points
4. **Disclaimer**: Remind user to consult healthcare professionals

Keep your response professional, accurate, and easy to understand."""

        try:
            response = llm.invoke(prompt)
            final_text = response.content if hasattr(response, 'content') else str(response)

            print(f"✅ Aggregator: Generated {len(final_text)} char response")

            return {
                **state,
                "final_answer": final_text
            }

        except Exception as e:
            print(f"❌ Aggregator LLM Error: {e}")
            # Fallback: return formatted results
            fallback = "\n\n".join(str(r) for r in results)
            return {
                **state,
                "final_answer": fallback
            }

    # ============================================
    # SINGLE-TOOL AGGREGATION
    # ============================================

    # RAG results - already formatted, return directly
    if tool == "rag":
        first_result = results[0] if results else ""
        print(f"✅ Aggregator: RAG response ({len(str(first_result))} chars)")
        return {
            **state,
            "final_answer": str(first_result)
        }

    # Research & WebSearch - Use LLM to summarize
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3
    )

    context = "\n\n".join(str(r) for r in results)

    if tool == "research":
        prompt = f"""Summarize these research papers for the query: "{query}"

{context}

Provide:
1. Overview of key findings
2. Important studies mentioned (with authors/journals)
3. Clinical implications
4. Disclaimer about consulting healthcare professionals

Keep it concise and organized."""

    elif tool == "websearch":
        prompt = f"""Summarize these medical news articles for: "{query}"

{context}

Provide:
1. 3-5 key news stories with brief descriptions
2. Recent developments or breakthroughs
3. Sources mentioned
4. Disclaimer about verifying with healthcare professionals

Keep it concise and organized."""

    else:
        # Generic summarization
        prompt = f"""Summarize this information for: "{query}"

{context}

Provide a clear, organized summary."""

    try:
        response = llm.invoke(prompt)
        final_text = response.content if hasattr(response, 'content') else str(response)

        print(f"✅ Aggregator: Generated {len(final_text)} char response")

        return {
            **state,
            "final_answer": final_text
        }

    except Exception as e:
        print(f"❌ Aggregator Error: {e}")
        # Fallback to raw context
        return {
            **state,
            "final_answer": context
        }