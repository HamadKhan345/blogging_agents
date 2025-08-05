from Tools.scraper import WebScraper
from Tools.search import Search
from Tools.featuredimage import FeaturedImageExtractor
from Markdown.toHTML import MarkdownToHTMLConverter
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI
import json
from google import genai
from google.genai import types


# Temp: Create a Testing directory to save the output files
import os
os.makedirs('./Testing', exist_ok=True)


load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# WebSearch which returns URLs based on a topic
current_urls = []

def WebSearch(inputs):
    global current_urls
    topic = inputs["topic"]
    max_results = inputs["max_results"]
    word_count = inputs["word_count"]

    # Search for URLs related to the topic
    search = Search()
    urls = search.search(topic, max_results)
    current_urls = urls
    return {'topic': topic, 'urls': urls, 'word_count': word_count}


# WebScrape which scrapes data from the URLs
def WebScrape(inputs):
    urls = inputs["urls"]
    word_count = inputs["word_count"]
    topic = inputs["topic"]
    scraper = WebScraper()
    data = scraper.scrape_multiple_urls(urls)
    print(scraper.get_summary_stats(data))

    #Temp: Save the scraped data to a JSON file
    # scraper.save_to_json(data, './Testing/blog_input_data.json')

    return {"topic": topic, "data": data, "word_count": word_count}


# Pydantic model
class BlogData(BaseModel):
    title: str = Field(..., description="Return Title of the blog, SEO optimized")
    excerpt: str = Field(..., max_length=200, description="Return Excerpt of the blog (max 150 characters)")
    content: str = Field(..., description="Return a Comprehensive, detailed and well-structured content of the blog in Markdown format")
    tags: list[str] = Field(..., description="Return List of Tags for the blog (max 10 tags)")

    @field_validator('excerpt', mode='before')
    @classmethod
    def truncate_excerpt(cls, v):
        if len(v) > 200:
            return v[:200].rstrip()
        return v
   

# Prompt template for generating the blog
template = PromptTemplate(
    template="""## ROLE & GOAL ##
You are an expert content creator, a seasoned blogger, and an SEO strategist. Your primary goal is to synthesize the provided research data into a single, cohesive, engaging, and original blog post. This post must be optimized for search engines and provide genuine value to the reader. You are writing for an intelligent audience that appreciates clear, well-structured, and insightful content. The blog can be upto {word_count} words or more depending on the data and the knowledge.

---

## CONTEXT ##
You will be given a `topic` and a JSON object `data` containing scraped content from top-ranking articles on that topic. This data is your research material. You must analyze, synthesize, and use it to build your own unique article.

**Topic:** "{topic}"
**Research Data:** "{data}"

---

## CRITICAL INSTRUCTIONS & WRITING STYLE ##
- **Originality is Paramount:** Do NOT simply rephrase or merge sentences from the source `data`. You must synthesize the core concepts and information into a new, unique, and well-written article. Your output must be original enough to pass plagiarism checks.
- **Human-like & Engaging Tone:** Write in a conversational yet authoritative voice. Use contractions (e.g., "it's", "you'll", "can't") to sound natural. Vary your sentence structure to maintain reader engagement.
- **SEO Optimization:**
    - The `title` must be catchy, compelling, and include the primary keyword from the topic.
    - Naturally weave the topic and related keywords throughout the `content`, especially in headings (H2, H3) and the first paragraph. Do not "keyword stuff."
- **Structure for Readability:**
    - The `content` must be well-structured using Markdown.
    - Use H2 tags (`##`) for main sections and H3 tags (`###`) for sub-sections.
    - Employ bullet points (`*` or `-`), numbered lists, and **bold text** to break up text and highlight key information.
- **Avoid AI Clichés:** Strictly avoid generic and robotic phrases like:
    - "In conclusion..."
    - "In today's fast-paced world..."
    - "The world of... is ever-evolving..."
    - "Unlocking the power of..."
    - "It's important to note that..."
    - Start the blog with a strong hook and end with a compelling summary or a final, insightful thought.
- **Value-Driven Content:** Focus on providing actionable advice, clear explanations, and unique insights derived from synthesizing the provided data. Go beyond the obvious to deliver real value.

---

## REQUIRED OUTPUT FORMAT ##
You MUST return your response as a single, raw JSON object that can be directly parsed. Do not add any explanatory text, comments, or markdown formatting like ```json before or after the JSON object. The JSON object must have the following keys:

- `title`: An SEO-optimized string for the blog title.
- `excerpt`: A concise, engaging summary. **Strictly maximum 200 characters.**
- `content`: The comprehensive, well-structured blog post in Markdown format, following all guidelines above.
- `tags`: A list of up to 10 relevant string tags.

Respond ONLY with this JSON object. Do NOT include any other text or formatting.
""",
    input_variables=["topic", "data", "word_count"],
)

# Model for generating the blog
# model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.5, max_tokens=65536, thinking_budget = 5000, max_retries=10)

# structured_model = model.with_structured_output(BlogData)

def call_gemini_with_structured_output(inputs):
    prompt = template.format(**inputs)
    client = genai.Client()

    config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=BlogData,
    temperature=0.5,
    maxOutputTokens=65536,
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )

    try:
        validated = response.parsed 
        return validated
    except Exception as e:
        raise ValueError(f"Error parsing Gemini output: {e}\nRaw output: {response.text}")
    


chain = RunnableSequence(
    RunnableLambda(WebSearch),
    RunnableLambda(WebScrape),
    RunnableLambda(call_gemini_with_structured_output),
)


# Fast Api endpoint to return the results
app = FastAPI()

class BlogRequest(BaseModel):
    topic: str
    max_results: int = 2
    word_count: int = 700
    scrape_thumbnail: bool = False

@app.post("/generate_blog")
async def generate_blog(request: BlogRequest):
    global current_urls


    output = chain.invoke({"topic": request.topic, "max_results": request.max_results, "word_count": request.word_count})
    
    # Temp: Save the output to a JSON file before conversion
    # with open('./Testing/blog_output_before.json', 'w') as f:
    #     json.dump(output.model_dump(), f, indent=4)

    # Convert Markdown to HTML
    toHTML = MarkdownToHTMLConverter()
    results = toHTML.convert_to_html(output)

    # Featured image extraction
    featured_image = None
    if request.scrape_thumbnail:
        extractor = FeaturedImageExtractor()
        featured_image = extractor.get_featured_image(current_urls)

    if featured_image is None:
        featured_image = {
            "success": False,
            "image_url": None,
        }
    
    combined_results = {
        "blog_data": results.model_dump(),
        "featured_image": featured_image
    }

    # Temp: Save the combined results to a JSON file
    # with open('./Testing/blog_output_converted_to_html.json', 'w') as f:
    #     json.dump(combined_results, f, indent=4)

    return combined_results


# uvicorn QuickResearch.quickresearch_exp:app --host 127.0.0.1 --port 8001 --reload