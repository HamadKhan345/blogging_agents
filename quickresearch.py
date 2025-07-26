from ddgs import DDGS
from scraper import WebScraper
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import bleach
import markdown
from fastapi import FastAPI

load_dotenv()


# WebSearch which returns URLs based on a topic
def WebSearch(inputs):
  topic = inputs["topic"]
  max_results = inputs["max_results"]
  with DDGS() as ddgs:
    results = ddgs.text(topic, max_results=max_results)
    urls = []
    for item in results:
        if "href" in item:
            urls.append(item["href"])
    return {'topic': topic, 'urls': urls}


# WebScrape which scrapes data from the URLs
def WebScrape(inputs):
    urls = inputs["urls"]
    scraper = WebScraper()
    data = scraper.scrape_multiple_urls(urls)
    print(scraper.get_summary_stats(data))
    # scraper.save_to_json(data, 'blog_input_data.json')
    return {"topic": inputs["topic"], "data": data}


# Pydantic model
class BlogData(BaseModel):
    title: str = Field(..., description="Title of the blog, SEO optimized")
    excerpt: str = Field(..., max_length=200, description="Excerpt of the blog (max 150 characters)")
    content: str = Field(..., description="Comprehensive and detailed content of the blog in Markdown format")
    tags: list[str] = Field(..., description="Tags for the blog (max 10 tags)")
   

# Prompt template for generating the blog
template = PromptTemplate(
    template=""" 
You are an expert human writer and editor. Your goal is to write a comprehensive, detailed, and well-structured blog on the topic: {topic} using the following data: {data}

Return your answer as a JSON object with these fields:
- title: string (the blog title, SEO optimized)
- excerpt: string (a summary, **no more than 150 characters**)
- content: string (the comprehensive and detailed blog content in markdown format)
- tags: list of strings (relevant tags, max 10 tags)

Make sure the excerpt is at most 150 characters. Return only the JSON object.
    """,
    input_variables=["topic", "data"]
)

# Model for generating the blog
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)

structured_model = model.with_structured_output(BlogData)

chain = RunnableSequence(
    RunnableLambda(WebSearch),
    RunnableLambda(WebScrape),
    template,
    structured_model,
)

# output = chain.invoke({"topic": "how to create html website, give me code", "max_results": 2})


# Function to convert Markdown content to HTML and clean it
def convert_to_html(output):
    html_content = markdown.markdown(output.content)
    allowed_tags = [
    'p', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'blockquote', 'a', 'br',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'code', 'pre', 's', 'img', 'video', 'div'
    ]
    clean_html = bleach.clean(html_content, tags=allowed_tags, strip=True)
    output.content = clean_html
    return output

# results = convert_to_html(output)




# Save the results to a JSON file
# with open('blog_output.json', 'w') as f:
#     json.dump(results.model_dump(), f, indent=4)

# Fast Api endpoint to return the results
app = FastAPI()

class BlogRequest(BaseModel):
    topic: str
    max_results: int = 2

@app.post("/generate_blog")
async def generate_blog(request: BlogRequest):
    output = chain.invoke({"topic": request.topic, "max_results": request.max_results})
    results = convert_to_html(output)
    return results.model_dump()