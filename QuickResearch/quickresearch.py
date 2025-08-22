from Tools.scraper import WebScraper
from Tools.search import Search
from Tools.featuredimage import FeaturedImageExtractor
from Google_Genai.googlegenai import google_structured_output
from Markdown.toHTML import MarkdownToHTMLConverter

from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
import json
import time
load_dotenv()


# WebSearch which returns URLs based on a topic
current_urls = []

def WebSearch(inputs):
    print("Searching for URLs related to the topic")
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
    print("Scraping data from the URLs")
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
blog_prompt = PromptTemplate(
    template="""
## ROLE & GOAL ##
You are an expert content creator, seasoned blogger, and SEO strategist.
Create an **original, engaging, and SEO-optimized blog** using the provided research data.
Audience: Intelligent readers who prefer clarity and actionable insights.
Aim for at least {word_count} words (you can exceed if needed).

---

## CONTEXT ##
Topic: {topic}  
Research Data:  
{data}

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
    input_variables=["topic", "data", "word_count"],
)



# Model for generating the blog
# model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.5, max_tokens=65536)

# structured_model = model.with_structured_output(BlogData)
def call_gemini_with_structured_output(inputs):
    prompt = blog_prompt.format(**inputs)
    structured_model = google_structured_output()
    
    
    # output = structured_model.call_google_structured_output(prompt=prompt, pydantic_model=BlogData, model="gemini-2.5-flash", max_tokens=15000, temperature=0.5)
    max_attempts = 4
    for attempt in range(max_attempts):
        try:   
            blog_data = structured_model.call_google_structured_output(prompt=prompt, pydantic_model=BlogData, model="gemini-2.0-flash", max_tokens=8100, thinking_budget=None)
            
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
    
    return blog_data


chain = RunnableSequence(
    RunnableLambda(WebSearch),
    RunnableLambda(WebScrape),
    RunnableLambda(call_gemini_with_structured_output),
)



def run_quick_research(topic: str, max_results: int = 2, word_count: int = 1000, scrape_thumbnail: bool = False):
    print("Running Quick Research for topic:", topic)
    inputs = {
        "topic": topic,
        "max_results": max_results,
        "word_count": word_count
    }
    try:
        output = chain.invoke(inputs)
        
        # Temp: Save the output to a JSON file before conversion
        # with open('./Testing/blog_output_before.json', 'w') as f:
        #     json.dump(output.model_dump(), f, indent=4)

        # Convert Markdown to HTML
        toHTML = MarkdownToHTMLConverter()
        content = toHTML.convert_to_html(output.content)
        output.content = content

        # Featured image extraction
        featured_image = None
        if scrape_thumbnail:
            extractor = FeaturedImageExtractor()
            featured_image = extractor.get_featured_image(current_urls)

        if featured_image is None:
            featured_image = {
                "success": False,
                "image_url": None,
            }
        
        combined_results = {
            "blog_data": output.model_dump(),
            "featured_image": featured_image
        }

        return combined_results
    except Exception as e:
        print(f"Error in run_quick_research: {e}")
        return None