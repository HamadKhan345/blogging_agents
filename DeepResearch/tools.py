from Tools.search import Search
from Tools.scraper import WebScraper
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Search Tool
class SearchTool(BaseModel):
    topic: str = Field(..., description="The search topic.")
    max_results: int = Field(10, description="The maximum number of results to return.")


search = Search()

web_search_tool = StructuredTool(
    name="WebSearch",
    description="Perform a DuckDuckGo search for the given topic and return the complete search results in a structured format.",
    func=search.search_complete,
    args_schema=SearchTool,
)
# Example
# results = web_search_tool.invoke({"topic": "Python programming", "max_results": 5})
# print(results)


# Web Scraper Tool
class WebScraperTool(BaseModel):
    urls: list[str] = Field(..., description="List of URLs to scrape.")

scraper = WebScraper()

web_scraper_tool = StructuredTool(
    name="WebScraper",
    description="Scrapes the content of the provided URLs and returns the scraped data in a structured format.",
    func=scraper.scrape_multiple_urls,
    args_schema=WebScraperTool,
)

# Example
# scraped_data = web_scraper_tool.invoke({"urls": ["https://www.thenews.com.pk/latest/1332324-us-imposes-19-duty-on-pakistan-imports-as-trump-widens-trade-crackdown"]})
# print(scraped_data)

all_tools = [web_search_tool, web_scraper_tool]





