from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from chromadb.utils import embedding_functions
import requests

app = FastAPI()

# Allow the HTML frontend to communicate with this local API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to the local ChromaDB we just built
print("Connecting to local database...")
client = chromadb.PersistentClient(path="chroma_db")
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name="black_london_archive", embedding_function=embedding_func)

class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_archive(request: QueryRequest):
    question = request.question
    print(f"Received query: {question}")
    
    # 1. Search ChromaDB for the top 3 most relevant transcript chunks
    results = collection.query(
        query_texts=[question],
        n_results=3 
    )
    
    context_chunks = results['documents'][0]
    metadata = results['metadatas'][0]
    
    # Stitch the chunks together for the AI to read
    context_text = "\n\n---\n\n".join(context_chunks)
    
    # 2. Instruct Ollama with a strict, anti-hallucination prompt
    prompt = f"""You are a curatorial assistant for the Black London archival collection. 
    Answer the user's question using ONLY the historical context provided below. 
    If the answer cannot be found in the context, explicitly state that the archive does not contain this information. Do not invent details.

    Context from Archive:
    {context_text}

    Question: {question}
    Answer:"""

    # 3. Send the prompt to the local Ollama application
    ollama_payload = {
        "model": "llama3.1", # Ensure this matches the model you pulled
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json=ollama_payload)
        response.raise_for_status()
        ollama_response = response.json().get("response", "Error reading AI response.")
    except Exception as e:
        ollama_response = f"Failed to connect to local Ollama AI. Is the Ollama app running? Error: {str(e)}"

    # 4. Return the AI's answer and the primary video citation to the frontend
    top_citation = metadata[0]
    
    return {
        "answer": ollama_response,
        "citations": [{
            "filename": top_citation["filename"],
            "time": top_citation["start_time"]
        }]
    }