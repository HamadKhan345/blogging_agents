import sys
sys.path.append(r'c:\Users\hamad\OneDrive\Desktop\FYP\AI System')

from QueryPlanner.planner import QueryPlanner
from Tools.search import Search
from Tools.scraper import WebScraper
from Tools.featuredimage import FeaturedImageExtractor
from Markdown.toHTML import MarkdownToHTMLConverter
from Google_Genai.googlegenai import google_structured_output

from langgraph.graph import StateGraph, START, END
from langchain.prompts import PromptTemplate
from typing import TypedDict, Optional
import time
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv()


class BlogState(TypedDict):
    topic: str
    word_count: int
    queries: list[str]
    urls: list[str]
    data: list[dict]
    summarized_results: dict[str, str]
    facts_to_verify: list[str]
    verified_facts: list[dict]
    title: str
    excerpt: str
    content: str
    tags: list[str]


class BlogSummary(BaseModel):
    summary: str = Field(..., description="A Comprehensive summary of the blog content, Make sure to include all the important points and details in the summary, and make it comprehensive and detailed")
    facts_to_verify: Optional[list[str]] = Field(None, description="A list of 1 or 2 important facts from the content that may need verification. Each fact should be a clear, searchable string suitable for searching on Google or DuckDuckGo. If there are no such facts, this field can be omitted.")


class FactVerification(BaseModel):
    fact: str = Field(..., description="Return the fact as it is, without any modifications.")
    comments: str = Field(..., description="Provide a brief explanation of the validity of the fact based on the search results.")


class BlogData(BaseModel):
    title: str = Field(..., description="Return Title of the blog, SEO optimized")
    excerpt: str = Field(..., max_length=200, description="Return Excerpt of the blog (max 200 characters)")
    content: str = Field(..., description="Return a Comprehensive, detailed and well-structured content of the blog in Markdown format")
    tags: list[str] = Field(..., description="Return List of Tags for the blog (max 10 tags)")

    @field_validator('excerpt', mode='before')
    @classmethod
    def truncate_excerpt(cls, v):
        if len(v) > 200:
            return v[:200].rstrip()
        return v
    

def generate_queries(state:BlogState):
    print("Generation Search Queries")
    planner = QueryPlanner()
    queries = planner.get_search_query(topic=state["topic"])
    print(f"Generated queries: {queries}")
    return {"queries": queries}


def get_urls(state: BlogState):
    print("Searching for URLs based on queries")
    search = Search()
    urls = search.search_list(state["queries"], max_results_per_topic=2)

    return {"urls": urls}
    
def scrape_data(state: BlogState):
    print("Scraping data from URLs")
    scraper = WebScraper()
    data = scraper.scrape_multiple_urls(state["urls"])
    print(scraper.get_summary_stats(data))

    return {"data": data}

def summarized_data(state: BlogState):
    print("Summarizing data")
    prompt_template = PromptTemplate(
        input_variables=["content"],
        template=(
            "Summarize the following content in a comprehensive and detailed manner. "
            "Include all important points, facts, and details from the text. "
            "Do not omit any relevant information; instead, condense and organize it clearly. "
            "Also list 1 or 2 facts that you think are important to verify from the content. "
            "If you include facts, make sure each is a clear, searchable string suitable for searching on Google or DuckDuckGo. "
            "You may omit this list if there are no such facts. "
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
        time.sleep(7)

    facts_to_verify = list(set(facts_to_verify))
      
    return {"summarized_results": summarized_results, "facts_to_verify": facts_to_verify}

def verify_facts(state: BlogState):
    print("Verifying facts")
    model = google_structured_output()
    prompt_template = PromptTemplate(
        input_variables=["fact", "metadata"],
        template = (
            "Fact to verify: {fact}\n"
            "Supporting information from DuckDuckGo search:\n{metadata}\n\n"
            "Based on the above search results, comment on the validity of the fact. "
            "Return the fact and your comments. "
        )
    )

    search = Search()
    verified_facts = []
    
    for fact in state.get("facts_to_verify", []):
        if not fact:
            continue
        results = search.search_list_complete([fact], max_results_per_topic=5)
        if results:
            metadata_str = "\n".join([str(item) for item in results]) if results else ""
            prompt = prompt_template.format(fact=fact, metadata=metadata_str)
            verification = model.call_google_structured_output(prompt=prompt, pydantic_model=FactVerification, model="gemini-2.5-flash")
            verified_facts.append(verification.model_dump())
            time.sleep(7)
      
    return {"verified_facts": verified_facts}


def generate_blog(state: BlogState):
    print("Generating blog content")


    prompt_template = PromptTemplate(
    template="""
## ROLE & GOAL ##
You are an expert content creator, seasoned blogger, and SEO strategist.
Create an **original, engaging, and SEO-optimized blog** using the provided research data.
Audience: Intelligent readers who prefer clarity and actionable insights.
Aim for at least {word_count} words (you can exceed if needed).

---

## CONTEXT ##
Topic: {topic}  
Summarized_Data:  
{summarized_results}

Verified Facts:
{verified_facts}

---

## CRITICAL INSTRUCTIONS ##
### PRIORITY ORDER ###
1. Originality & factual accuracy
2. Clear, engaging, human-like writing
3. SEO optimization and readability

### WRITING RULES ###
- **Originality:** Do NOT copy or merge sentences. Rewrite ideas uniquely.
- **Accuracy:** Stick to the given data. Never invent facts.
- **Style:** Conversational, authoritative, 12th-grade reading level.
- Use contractions for natural tone.
- Start with a strong hook (fact, question, or insight).
- Avoid clickbait intros and AI clichés like:
    - "In conclusion..."
    - "In today's fast-paced world..."
    - "Unlocking the power of..."
- Ensure logical flow and readability.

### STRUCTURE & MARKDOWN ###
- Use Markdown for full structure:
    - `##` for main sections, `###` for subsections.
    - Bullet points, numbered lists, and **bold text** for emphasis.
    - Where helpful, include:
        * **Tables** for comparisons or structured data.
        * **Blockquotes (`>`)** for expert tips or key highlights.
        * **Inline code** for terms or examples (`like this`).
        * **Fenced code blocks** for multi-line examples.


### SEO RULES ###
- Include the main keyword in the title and first 100 words.
- Use related keywords naturally in headings and body (1–2% density).
- Generate meta description under 160 characters.
- Ensure scannable sections with headings and visual elements.

---

""",
    input_variables=["topic", "summarized_results", "verified_facts", "word_count"],
)
    prompt = prompt_template.format(
        topic=state["topic"],
        summarized_results=state["summarized_results"],
        verified_facts=state["verified_facts"],
        word_count=state["word_count"]
    )
    model = google_structured_output()
    blog_data = None
    max_attempts = 4
    for attempt in range(max_attempts):
        try:   
            blog_data = model.call_google_structured_output(prompt=prompt, pydantic_model=BlogData, model="gemini-2.0-flash", max_tokens=8100, thinking_budget=None)
            
            if (blog_data
                    and getattr(blog_data, "title", None)
                    and getattr(blog_data, "content", None)
                    and getattr(blog_data, "excerpt", None)
                    and getattr(blog_data, "tags", None)
                    and isinstance(getattr(blog_data, "tags", None), list)
                    and len(getattr(blog_data, "tags", [])) > 0
                ):
               break
            raise ValueError("Model returned None or incomplete BlogData")
        
        except Exception as e:
            print(f"Error generating blog content: {e}")
            if attempt < max_attempts - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise e

    return {"title": blog_data.title, "excerpt": blog_data.excerpt, "content": blog_data.content, "tags": blog_data.tags}

def convert_output(state: BlogState):
    print("Converting blog content to HTML")
    convert = MarkdownToHTMLConverter()
    html_content = convert.convert_to_html(state["content"])
    return {"content": html_content}
    
    
graph = StateGraph(BlogState)

graph.add_node('generate_queries', generate_queries)
graph.add_node('get_urls', get_urls)
graph.add_node('scrape_data', scrape_data)
graph.add_node('summarized_data', summarized_data)
graph.add_node('verify_facts', verify_facts)
graph.add_node('generate_blog', generate_blog)
graph.add_node('convert_output', convert_output)


graph.add_edge(START, 'generate_queries')
graph.add_edge('generate_queries', 'get_urls')
graph.add_edge('get_urls', 'scrape_data')
graph.add_edge('scrape_data', "summarized_data")
graph.add_edge('summarized_data', 'verify_facts')
graph.add_edge('verify_facts', 'generate_blog')
graph.add_edge('generate_blog', 'convert_output')
graph.add_edge('convert_output', END)
workflow = graph.compile()



def run_deep_research(topic: str, max_results: int = 2, word_count: int = 1000, scrape_thumbnail: bool = False):
    print("Running Deep Research for topic:", topic)
    initial_state = {
        "topic": topic,
        "word_count": word_count
    }
    try:
        results = workflow.invoke(initial_state)

        blog_data = {
        "title": results.get("title"),
        "excerpt": results.get("excerpt"),
        "content": results.get("content"),
        "tags": results.get("tags")
        }

        # Featured image extraction
        featured_image = None
        if scrape_thumbnail:
            extractor = FeaturedImageExtractor()
            featured_image = extractor.get_featured_image(results.get("urls", []))

        if featured_image is None:
            featured_image = {
                "success": False,
                "image_url": None,
            }
        
        
        combined_results = {
            "blog_data": blog_data,
            "featured_image": featured_image
        }

        return combined_results
    except Exception as e:
        print(f"Error in run_deep_research: {e}")
        return None