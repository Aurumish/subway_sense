from exa_py import Exa
from cerebras.cloud.sdk import Cerebras
import os
from dotenv import load_dotenv
# from google import genai
# from google.genai import types
from pathlib import Path

# Load .env file from the script's directory to ensure keys are loaded
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

EXA_API_KEY = os.getenv("EXA_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = Cerebras(api_key=CEREBRAS_API_KEY)
exa = Exa(api_key=EXA_API_KEY)
# gemini_client = genai.Client(api_key=GEMINI_API_KEY)

print("✅ Setup complete")

def search_web(query, num=5):
    """Search the web using Exa's auto search"""
    result = exa.search_and_contents(
      query,
      type = "auto",
      num_results = num,
      text={"max_characters": 1000}
    )
    return result.results
    
search_web("Find the most recent NYC PD news updates that concern citizens wellbeing, safety, and awareness.")

print("✅ Search function ready")

def ask_ai(prompt):
    """Get AI response from Cerebras"""
    chat_completion = client.chat.completions.create(
      messages=[
          {
              "role": "user",
              "content": prompt,
          }
      ],
      model="llama-4-scout-17b-16e-instruct",
      max_tokens = 600,
      temperature = 0.2
    )
    return chat_completion.choices[0].message.content
prompt = ("Based on the results found from the web, compile a short comprehensive report of any local violence. Frame your report by providing the address of the event and cross-check it's proximity to the nearest subway station. Include the time of the event + the contents and what happened.")

print("✅ AI function ready")

def research_topic(query):
    """Main research function that orchestrates the entire process"""
    print(f"🔍 Researching: {query}")

    # Search for sources
    results = search_web(query, 5)
    print(f"📊 Found {len(results)} sources")

    # Get content from sources
    sources = []
    for result in results:
        content = result.text
        title = result.title
        if content and len(content) > 200:
            sources.append({
                "title": title,
                "content": content
            })

    print(f"📄 Scraped {len(sources)} sources")

    if not sources:
        return {"summary": "No sources found", "insights": []}

    # Create context for AI analysis
    context = f"Research query: {query}\n\nSources:\n"
    for i, source in enumerate(sources[:4], 1):
        context += f"{i}. {source['title']}: {source['content'][:400]}...\n\n"
        # ^^ get rid of this to use API params!
        # best practices - https://www.anthropic.com/engineering/built-multi-agent-research-system

    # Ask AI to analyze and synthesize
    prompt = f"""{context}

A list of important violent/potentially dangerous events, the time at which they happened, and most importantly: the subway station which they occured near.

Format your response exactly like this:

LIST
- [item 1], [time of event], [subway station]
- [item 2], [time of event], [subway station]
- [item 3], [time of event], [subway station
"""

    response = ask_ai(prompt)
    print("🧠 Analysis complete")

    return {"query": query, "sources": len(sources), "response": response}

print("✅ Research function ready")

# def generate(prompt):
#     """Generate content using the Gemini API."""
#     contents = [
#         types.Content(
#             role="user",
#             parts=[
#                 types.Part.from_text(text=prompt),
#             ],
#         ),
#     ]

#     response = gemini_client.models.generate_content(
#         model="gemini-1.5-flash",
#         contents=contents,
#     )
#     return response.text

# def verify_with_gemini(sources, cerebras_report):
#     """Verify the Cerebras report using Gemini, following the correct API pattern."""
#     print("🤖 Verifying with Gemini...")
    
#     source_text = ""
#     for i, source in enumerate(sources, 1):
#         source_text += f"Source {i}: {source['title']}\n{source['content']}\n\n"

#     prompt_text = f"""Please review the following sources and verify the accuracy of the summary report. If the report is accurate, return it as is. If there are inaccuracies or missing information, please correct the report and return a more accurate version.

# Sources:
# {source_text}

# Report to Verify:
# {cerebras_report}
# """
    
#     return generate(prompt_text)

def deeper_research_topic(station_name):
    """Two-layer research for better depth"""
    query = f"recent crime and safety incidents near {station_name} subway station in NYC within the last 24 hours"
    print(f"🔍 Researching: {query}")

    # Layer 1: Initial search
    results = search_web(query, 6)
    sources = []
    for result in results:
        if result.text and len(result.text) > 200:
            sources.append({"title": result.title, "content": result.text})

    print(f"Layer 1: Found {len(sources)} sources")

    if not sources:
        return {"summary": "No sources found", "insights": []}

    # Get initial analysis and identify follow-up topic
    context1 = f"Research query: {query}\n\nSources:\n"
    for i, source in enumerate(sources[:4], 1):
        context1 += f"{i}. {source['title']}: {source['content'][:300]}...\n\n"

    follow_up_prompt = f"""{context1}

Based on these sources, what's the most important follow-up question that would deepen our understanding of "{query}"?

Respond with just a specific search query (no explanation):"""

    follow_up_query = ask_ai(follow_up_prompt).strip().strip('"')

    # Layer 2: Follow-up search
    print(f"Layer 2: Investigating '{follow_up_query}'")
    follow_results = search_web(follow_up_query, 4)

    for result in follow_results:
        if result.text and len(result.text) > 200:
            sources.append({"title": f"[Follow-up] {result.title}", "content": result.text})

    print(f"Total sources: {len(sources)}")

    # Final synthesis
    all_context = f"Research query: {query}\nFollow-up: {follow_up_query}\n\nAll Sources:\n"
    for i, source in enumerate(sources[:7], 1):
        all_context += f"{i}. {source['title']}: {source['content'][:300]}...\n\n"

    final_prompt = f"""{all_context}

Provide a comprehensive analysis:

SUMMARY: A list of important violent/potentially dangerous events, the time at which they happened, and most importantly: the subway station which they occured near. Additionally, provide the source from which you pulled.

Format your response exactly like this:

LIST
- [item 1], [time of event], [subway station]
- [item 2], [time of event], [subway station]
- [item 3], [time of event], [subway station
""" 

    response = ask_ai(final_prompt)
    
    # Verify with Gemini
    # verified_response = verify_with_gemini(sources, response)
    
    return {"query": query, "sources": len(sources), "response": response}

print("✅ Enhanced research function ready")

if __name__ == '__main__':
    # Example usage:
    result = deeper_research_topic("Times Square")
    print(result)
