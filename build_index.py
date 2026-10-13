import os
import json
import chromadb
from chromadb.utils import embedding_functions

# 1. Define folder paths relative to this script
TRANSCRIPTS_DIR = "transcripts"
DB_DIR = "chroma_db"

def build_database():
    print("Initialising local ChromaDB...")
    
    # 2. Set up the local Chroma database and the embedding model
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # We use all-MiniLM-L6-v2 as it is fast, lightweight, and runs entirely locally
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Create or load the collection
    collection = client.get_or_create_collection(
        name="black_london_archive", 
        embedding_function=embedding_func
    )
    
    # 3. Read through the transcripts folder
    files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.json')]
    print(f"Found {len(files)} JSON transcripts. Processing...")

    total_chunks_added = 0

    for filename in files:
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)
        reel_id = filename.replace('.json', '').replace('BLACKLIVES_', '') # e.g., BL_001
        
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            # Whisper outputs an array of 'segments'. We will group them to give the AI more context.
            segments = data.get('segments', [])
            
            # Group every 5 segments together (roughly 20-30 seconds of continuous speech)
            GROUP_SIZE = 5
            
            docs = []
            metadatas = []
            ids = []
            
            for i in range(0, len(segments), GROUP_SIZE):
                chunk = segments[i:i + GROUP_SIZE]
                
                # Combine the text
                combined_text = " ".join([seg['text'].strip() for seg in chunk])
                
                # Grab the start time of the first segment in this chunk
                start_time = chunk[0]['start']
                
                # Create a unique ID for this chunk
                chunk_id = f"{reel_id}_chunk_{i}"
                
                docs.append(combined_text)
                metadatas.append({
                    "reel_id": reel_id,
                    "start_time": int(start_time), # Save as integer for the HTML player
                    "filename": filename.replace('.json', '.mp4')
                })
                ids.append(chunk_id)
            
            # 4. Insert the grouped chunks into ChromaDB
            if docs:
                collection.add(
                    documents=docs,
                    metadatas=metadatas,
                    ids=ids
                )
                total_chunks_added += len(docs)
                print(f"Indexed {reel_id}: Added {len(docs)} chunks.")

    print(f"\nSuccess! Database build complete.")
    print(f"Total contextual chunks embedded: {total_chunks_added}")
    print(f"Data saved to: ./{DB_DIR}/")

if __name__ == "__main__":
    build_database()