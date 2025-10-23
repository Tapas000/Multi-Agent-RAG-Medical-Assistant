"""
RAG Agent — part of the Medical Chatbot AI System
------------------------------------------------
Uses FAISS + Groq LLM to answer disease/symptom-related queries.
"""

import os
from langchain_groq import ChatGroq
from src.tools.rag.retriever import retrieve_semantic_results

def rag_agent(state: dict):
    """
    LangGraph-compatible node.
    Uses FAISS semantic retrieval + Groq LLM summarization.
    """
    query = state.get("query", "")
    print(f"🧠 [RAG Agent] Processing query: {query}")

    # Debug: Print incoming state
    print(f"🔍 [RAG Agent] Incoming state keys: {state.keys()}")

    # Step 1: Retrieve from FAISS
    results = retrieve_semantic_results(query, k=3)

    print(f"🔍 [RAG Agent] Retrieved {len(results) if results else 0} documents")

    if not results:
        print("⚠️ [RAG Agent] No results found")
        return {
            **state,
            "results": ["No relevant disease or symptom data found in the knowledge base."]
        }

    # Step 2: Summarize with LLM
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY")
    )

    context = "\n\n".join(results)
    prompt = f"""You are a medical assistant.
Based on the following retrieved disease-symptom information, answer the user's query clearly.

User Query:
{query}

Retrieved Information:
{context}

Answer:
- Mention likely diseases or conditions
- List main symptoms and treatments
- Keep explanation concise and factual
- Always recommend consulting a healthcare professional for diagnosis
"""

    try:
        response = llm.invoke(prompt)

        # Extract content properly
        final_answer = response.content if hasattr(response, 'content') else str(response)

        print(f"✅ [RAG Agent] Generated response ({len(final_answer)} chars)")
        print(f"🔍 [RAG Agent] Response preview: {final_answer[:100]}...")

        # CRITICAL: Create return dict
        return_dict = {
            **state,
            "results": [final_answer]
        }

        # Debug: Verify what we're returning
        print(f"🔍 [RAG Agent] Returning results list length: {len(return_dict['results'])}")
        print(f"🔍 [RAG Agent] First result type: {type(return_dict['results'][0])}")
        print(f"🔍 [RAG Agent] First result length: {len(return_dict['results'][0])}")

        return return_dict

    except Exception as e:
        print(f"❌ [RAG Agent] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "results": [f"Error generating response: {str(e)}"]
        }