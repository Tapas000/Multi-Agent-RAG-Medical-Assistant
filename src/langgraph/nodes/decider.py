"""
Fixed Decider Node - Properly detects multi-intent queries
"""

def decide_tool(state):
    """
    Smart routing with proper multi-tool detection
    """
    query = state["query"].lower()
    original_query = state["query"]

    # Initialize metadata if not exists
    if "metadata" not in state:
        state["metadata"] = {}

    print(f"🔍 Analyzing: '{original_query}'")

    # ===========================================
    # INTENT DETECTION
    # ===========================================

    # Personal health indicators
    has_personal = any(phrase in query for phrase in [
        "i have", "i'm", "i am", "my", "suffering",
        "experiencing", "diagnosed", "i feel"
    ])

    # Research/study indicators
    has_research = any(word in query for word in [
        "research", "study", "studies", "paper", "papers",
        "clinical trial", "trials", "scientific", "evidence",
        "findings", "publication", "literature"
    ])

    # News/updates indicators
    has_news = any(word in query for word in [
        "latest", "recent", "new", "today", "current",
        "update", "updates", "breakthrough", "2024", "2025",
        "news", "announcement", "guideline"
    ])

    # Medical info indicators (RAG)
    has_medical_info = any(word in query for word in [
        "treatment", "symptom", "disease", "condition",
        "cure", "cause", "prevent", "diagnosis", "options",
        "what is", "how to", "tell me about"
    ])

    # Conjunction check (indicates multiple intents)
    has_conjunction = any(word in query for word in [
        " and ", " also ", " plus ", " as well as "
    ])

    print(f"   Personal: {has_personal}")
    print(f"   Research: {has_research}")
    print(f"   News: {has_news}")
    print(f"   Medical Info: {has_medical_info}")
    print(f"   Conjunction: {has_conjunction}")

    # ===========================================
    # MULTI-TOOL PATTERNS
    # ===========================================

    # Pattern 1: Personal health + Research
    # "I have diabetes and want research papers"
    if has_personal and has_research:
        medical_topic = extract_topic(original_query)
        state["tool"] = "multi"
        state["metadata"] = {
            "multi_tool": True,
            "tools": ["rag", "research"],
            "queries": {
                "rag": original_query,
                "research": f"{medical_topic} research"
            }
        }
        print(f"🔀 MULTI-TOOL: Personal + Research")
        return state

    # Pattern 2: Medical info + Research (YOUR CASE!)
    # "heart disease treatment options and latest studies"
    if has_medical_info and has_research and has_conjunction:
        medical_topic = extract_topic(original_query)
        state["tool"] = "multi"
        state["metadata"] = {
            "multi_tool": True,
            "tools": ["rag", "research"],
            "queries": {
                "rag": original_query,
                "research": f"{medical_topic} research"
            }
        }
        print(f"🔀 MULTI-TOOL: Medical Info + Research")
        return state

    # Pattern 3: Medical info + News
    # "diabetes symptoms and latest news"
    if has_medical_info and has_news and has_conjunction:
        medical_topic = extract_topic(original_query)
        state["tool"] = "multi"
        state["metadata"] = {
            "multi_tool": True,
            "tools": ["rag", "websearch"],
            "queries": {
                "rag": original_query,
                "websearch": f"{medical_topic} latest news"
            }
        }
        print(f"🔀 MULTI-TOOL: Medical Info + News")
        return state

    # Pattern 4: Research + News
    # "cancer research and latest updates"
    if has_research and has_news:
        medical_topic = extract_topic(original_query)
        state["tool"] = "multi"
        state["metadata"] = {
            "multi_tool": True,
            "tools": ["research", "websearch"],
            "queries": {
                "research": f"{medical_topic} research",
                "websearch": f"{medical_topic} latest news"
            }
        }
        print(f"🔀 MULTI-TOOL: Research + News")
        return state

    # ===========================================
    # SINGLE-TOOL ROUTING
    # ===========================================

    # Personal symptoms (high priority)
    if has_personal:
        state["tool"] = "rag"
        print(f"🎯 SINGLE: RAG (personal symptom)")
        return state

    # Explicit research request
    if has_research and not has_medical_info:
        state["tool"] = "research"
        print(f"🎯 SINGLE: Research")
        return state

    # News/updates
    if has_news and not has_medical_info:
        state["tool"] = "websearch"
        print(f"🎯 SINGLE: WebSearch")
        return state

    # Medical information (default)
    if has_medical_info:
        state["tool"] = "rag"
        print(f"🎯 SINGLE: RAG (medical info)")
        return state

    # Fallback to RAG
    state["tool"] = "rag"
    print(f"🎯 SINGLE: RAG (default fallback)")
    return state


def extract_topic(query):
    """Extract core medical topic from query"""
    # Remove common noise words
    noise = [
        "i have", "i want", "i need", "show me", "find me",
        "give me", "tell me", "and", "latest", "recent",
        "research", "papers", "studies", "news", "update",
        "treatment options", "about", "information"
    ]

    cleaned = query.lower()
    for word in noise:
        cleaned = cleaned.replace(word, " ")

    # Clean whitespace and return
    cleaned = " ".join(cleaned.split()).strip()
    return cleaned if cleaned else query.split()[0]