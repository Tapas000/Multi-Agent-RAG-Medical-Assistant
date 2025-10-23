import os
import requests
from typing import Dict


def research_agent(state: Dict) -> Dict:
    """
    Searches EuropePMC for research papers.
    """
    query = state.get("query", "")
    print(f"🔍 Searching EuropePMC for: {query}")

    # EuropePMC API endpoint
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params = {
        "query": query,
        "format": "json",
        "pageSize": 5,
        "cursorMark": "*"
    }

    try:
        print(f"🔍 Debug - Making request to EuropePMC...")
        response = requests.get(base_url, params=params, timeout=10)
        print(f"🔍 Debug - Status code: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        print(f"🔍 Debug - Response keys: {data.keys()}")
        print(f"🔍 Debug - Hit count: {data.get('hitCount', 0)}")

        # Extract results
        results_list = data.get("resultList", {}).get("result", [])
        print(f"🔍 Debug - Results list length: {len(results_list)}")

        if not results_list:
            print("⚠️ Research: No papers found")
            return {
                **state,
                "results": [f"No research papers found for '{query}'. Try more specific medical terms."]
            }

        # Format results
        formatted_results = []
        for paper in results_list[:5]:
            title = paper.get("title", "No title")
            authors = paper.get("authorString", "Unknown authors")
            journal = paper.get("journalTitle", "Unknown journal")
            pub_year = paper.get("pubYear", "Unknown year")
            doi = paper.get("doi", "")
            pmid = paper.get("pmid", "")
            abstract = paper.get("abstractText", "No abstract available")

            # Truncate abstract if too long
            if len(abstract) > 300:
                abstract = abstract[:300] + "..."

            result_str = f"""**{title}**
Authors: {authors}
Journal: {journal} ({pub_year})
PMID: {pmid}
DOI: {doi}

Abstract: {abstract}
"""
            formatted_results.append(result_str)

        print(f"✅ Research: Found {len(formatted_results)} papers")

        # CRITICAL: Add debug before returning
        return_dict = {
            **state,
            "results": formatted_results
        }
        print(f"🔍 Debug - Returning {len(return_dict['results'])} results")

        return return_dict

    except requests.exceptions.Timeout:
        print("❌ Research: Request timeout")
        return {
            **state,
            "results": ["EuropePMC request timed out. Please try again."]
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ Research: Request error - {e}")
        return {
            **state,
            "results": [f"Error searching EuropePMC: {str(e)}"]
        }

    except Exception as e:
        print(f"❌ Research: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "results": [f"Error processing research papers: {str(e)}"]
        }


if __name__ == "__main__":
    test_state = {
        "query": "alzheimer's disease treatment",
        "tool": "research",
        "results": [],
        "metadata": {},
        "final_answer": ""
    }

    result = research_agent(test_state)
    print("\n📚 Research Results:\n")
    for i, paper in enumerate(result["results"], 1):
        print(f"\n{i}. {paper}")