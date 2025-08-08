import sys
sys.path.append(r'c:\Users\hamad\OneDrive\Desktop\FYP\AI System')

from QueryPlanner.planner import QueryPlanner
from Tools.search import Search
from Tools.scraper import WebScraper
from Google_Genai.googlegenai import google_structured_output

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI
from dotenv import load_dotenv
# load_dotenv()

class BlogState(TypedDict):
    topic: str
    queries: list[str]
    urls: list[str]
    data: list[dict]
    summarized_results: dict[str, str]
    facts_to_verify: list[str]
    verified_facts: list[str]
    title: str
    excerpt: str
    content: str
    tags: list[str]


class BlogSummary(BaseModel):
    summary: str = Field(..., description="A Comprehensive summary of the blog content, Make sure to include all the important points and details in the summary, and make it comprehensive and detailed")
    facts_to_verify: list[str] = Field(..., description="List a number of facts that you think are important to verify from the content")


def generate_queries(state:BlogState):
    planner = QueryPlanner()
    queries = planner.get_search_query(state["topic"])

    return {"queries": queries}


def get_urls(state: BlogState):
    search = Search()
    urls = search.search_list(state["queries"])

    return {"urls": urls}
    
def scrape_data(state: BlogState):
    scraper = WebScraper()
    data = scraper.scrape_multiple_urls(state["urls"])
    print(scraper.get_summary_stats(data))

    return {"data": data}

def summarized_data(state: BlogState):
    prompt_template = PromptTemplate(
        input_variables=["content"],
        template=(
            "Summarize the following content in a comprehensive and detailed manner. "
            "Include all important points, facts, and details from the text. "
            "Do not omit any relevant information; instead, condense and organize it clearly. "
            "Also list a number of facts that you think are important to verify from the content. "
            "Here is the content:\n\n{content}"
        )
    )
    # model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # structured_model = model.with_structured_output(BlogSummary)
    model = google_structured_output()
    summarized_results: dict[str, str] = {}
    facts_to_verify: list[str] = []
    for item in state.get("data", []):
        title = (item.get("title") or "").strip()
        content = (item.get("main_content") or "").strip()
        if not title or not content:
            continue 
        prompt = prompt_template.format(content=content)
        summary = model.call_google_structured_output(prompt=prompt, pydantic_model=BlogSummary, model="gemini-2.5-flash")
        # summary = structured_model.invoke(prompt)
        summarized_results[title]  = summary.summary
        if summary.facts_to_verify:  
            facts_to_verify.extend(summary.facts_to_verify)

    facts_to_verify = list(set(facts_to_verify))
      
    return {"summarized_results": summarized_results, "facts_to_verify": facts_to_verify}


graph = StateGraph(BlogState)

graph.add_node('generate_queries', generate_queries)
graph.add_node('get_urls', get_urls)
graph.add_node('scrape_data', scrape_data)
graph.add_node('summarized_data', summarized_data)
# graph.add_node('check_facts', check_facts)
# graph.add_node('verify_facts', verify_facts)
# graph.add_node('generate_blog', generate_blog)
# graph.add_node('check_output', check_output)
# 

graph.add_edge(START, 'generate_queries')
graph.add_edge('generate_queries', 'get_urls')
graph.add_edge('get_urls', 'scrape_data')
graph.add_edge('scrape_data', "summarized_data")
graph.add_edge('summarized_data', END)
workflow = graph.compile()


initial_state = {"topic": "Einstein theory of relativity"}

results = workflow.invoke(initial_state)