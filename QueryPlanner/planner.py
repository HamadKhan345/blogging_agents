from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class OutputFormatter(BaseModel):
    queries: list[str] = Field(
        ..., 
        max_items=5, 
        description="List of 5 search queries generated for the topic"
    )


class QueryPlanner:

    def __init__(self):
        self.prompt = PromptTemplate(
            template="""
You are an expert research analyst and content strategist. Your primary task is to break down a broad topic into a set of targeted search queries that will be used to gather information for a comprehensive, in-depth, and engaging blog post.

For the given topic, generate exactly 5 distinct search queries. These queries should be designed to cover the topic from multiple perspectives to ensure the final article is well-rounded and informative.

The set of 5 queries should aim to cover:

1) A foundational/definitional query: To understand the core concepts.

2) A "how-to" or practical application query: To provide actionable advice to the reader.

3) A query for specific sub-topics or common questions: To dive deeper into the details.

4) A query for data, statistics, or case studies: To find evidence and support claims.

5) A query exploring a unique angle, controversy, expert opinions, or future trends: To make the article stand out.

Topic: {topic}
""",
            input_variables=["topic"]
        )

        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)
        self.structured_model = self.model.with_structured_output(OutputFormatter)
        self.chain = RunnableSequence(self.prompt | self.structured_model)

    def get_search_query(self, topic: str):
        result = self.chain.invoke({"topic": topic})
        return result.queries
