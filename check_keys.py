
import os
from dotenv import load_dotenv

load_dotenv()

tavily = os.getenv("TAVILY_API_KEY")
serpapi = os.getenv("SERPAPI_KEY")
groq = os.getenv("GROQ_API_KEY")

print(f"TAVILY_API_KEY set: {bool(tavily)}")
print(f"SERPAPI_KEY set: {bool(serpapi)}")
print(f"GROQ_API_KEY set: {bool(groq)}")
