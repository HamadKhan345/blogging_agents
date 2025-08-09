from fastapi import FastAPI, Request
from QuickResearch.quickresearch_exp import run_quick_research
from DeepResearch.deepresearch import run_deep_research
from pydantic import BaseModel


app = FastAPI()

class BlogRequest(BaseModel):
    topic: str
    max_results: int = 2
    word_count: int = 1000
    scrape_thumbnail: bool = False
    method: str = "quick"


@app.post("/generate_blog")
async def generate_blog(request: BlogRequest):
    if request.method == "quick":
        result = run_quick_research(
            topic=request.topic,
            max_results=request.max_results,
            word_count=request.word_count,
            scrape_thumbnail=request.scrape_thumbnail
        )
    elif request.method == "deep":
        result = run_deep_research(
            topic=request.topic,
            word_count=request.word_count,
            scrape_thumbnail=request.scrape_thumbnail
        )
    else:
        return {"error": "Invalid method specified. Use 'quick' or 'deep'."}

    return result


# uvicorn main:app --host 127.0.0.1 --port 8001 --reload