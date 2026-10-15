# SYA #BlackLives: The Black London Collection – Local RAG Architecture

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23351532.svg)](https://doi.org/10.5281/zenodo.23351532)

> **Status: proof of concept.** This repository documents a working prototype, not a production system. See [Limitations](#limitations) before relying on its output.

## Project Overview

This repository contains an on-premises iteration of the architecture and documentation for the "Black London" audiovisual archive (1991–1993) retrieval system. The original prototype relied on a proprietary cloud video platform for hosting and metadata indexing, and proved vulnerable to third-party platform deprecation and data loss.

To improve long-term archival resilience, data sovereignty and privacy, the system has been re-architected as an open-source Retrieval-Augmented Generation (RAG) stack that runs on a single local machine. **Once set up, it requires no internet connection and sends no data to external services.**

## Architectural Approach

The system decouples the video assets from the search layer. It converts spoken audio into text, embeds that text in a locally hosted vector database, and uses a local Large Language Model (LLM) to answer natural-language queries from the retrieved transcript excerpts.

<img width="1342" height="869" alt="RAG architecture diagram" src="https://github.com/user-attachments/assets/5a9832f5-1868-4ad4-acc5-d13eca1db15a" />

The workflow is divided into three layers:

1. **Frontend (presentation and media):** a lightweight HTML/JavaScript interface that handles user queries and controls local media playback.
2. **Backend (middleware):** a Python API that routes the user's query, retrieves relevant transcript excerpts and oversees answer generation.
3. **AI and data layer:** locally run models and databases that transcribe audio, embed text and generate answers.

The proof-of-concept deployment looks like this:

<img width="1883" height="830" alt="Proof-of-concept deployment diagram" src="https://github.com/user-attachments/assets/c48e81de-5404-4a15-95f3-b0dcb1034bf0" />

## Tooling Context and Justification

The following open-source stack is used so that the archive does not feed external commercial models and remains usable without internet access.

### 1. Audio Transcription: OpenAI Whisper (local)

Legacy media must be transcribed before it can be searched. Whisper is run locally from the command line to batch-process the raw video files. It outputs structured JSON containing start and end timestamps for each segment, which keeps the text linked to positions in the video.

Whisper's output is machine-generated and has not been manually verified. Accuracy on archival audio, regional accents, dialect and proper names may be uneven.

### 2. Vector Database: ChromaDB and Sentence Transformers

Rather than a relational database, the system uses ChromaDB, a lightweight local vector database. Whisper transcripts are segmented into chunks and converted into vectors using a Hugging Face embedding model (`all-MiniLM-L6-v2`). This enables semantic search: the system can match the meaning of a question to relevant passages without relying on exact keywords.

### 3. Local Generation: Ollama

Ollama runs LLMs locally on the host machine. When a user asks a question, the three most relevant transcript chunks are sent to the local model (Llama 3.1 in this prototype) with an instruction to answer using only that context and to say so if the answer is not present.

This is a prompt-level safeguard. It reduces, but does not eliminate, the risk of the model adding unsupported information, particularly with smaller models.

### 4. Application Programming Interface: Python (FastAPI)

A lightweight Python server bridges the database, the model and the user. It receives the query from the web interface, retrieves matching chunks from ChromaDB, prompts Ollama and returns the answer with a video citation.

### 5. Media Delivery: HTML5 and localhost (for example, MAMP)

The frontend uses standard HTML5 video. Because the videos and application are hosted locally, the interface can use the timecode returned by the API. When a user clicks a citation, JavaScript loads the corresponding video and seeks to the start of the cited segment.

## Hardware Requirements and Scalability

Running the full pipeline locally requires capable hardware. Performance depends on processor architecture and available memory.

- **Processor:** Apple Silicon (M1 or later) is recommended. Its unified memory architecture allows Ollama and Whisper to use GPU acceleration through Apple's Metal framework. Intel-based machines can run the stack, but transcription and generation will be considerably slower.
- **16 GB RAM (recommended baseline):** sufficient to run a 7B or 8B parameter model, such as Llama 3.1, alongside Whisper and the operating system without heavy swapping.
- **8 GB RAM (minimum):** workable with smaller models, but expect slowdowns during generation.
- **32 GB RAM or more:** allows larger models (32B and above) and more accurate Whisper models such as `large-v3`.

*Scalability note:* the architecture can adapt to the available hardware. This proof of concept uses the Whisper `small` model to balance accuracy and memory use on standard consumer machines. It has not been tested on large archives.

## System Deployment and Portability

To deploy on a second machine without repeating transcription and indexing, follow this workflow.

### 1. Check the Target Hardware

Confirm that the new machine meets the baseline above.

### 2. Transfer the Project Directory

Copy the entire project directory, which must include:

- the `vimeo_downloads` directory containing the `.mp4` video files;
- the `transcripts` directory containing the Whisper `.json` files;
- the `chroma_db` directory containing the pre-computed vectors;
- the Python backend scripts and HTML/JavaScript frontend files.

### 3. Install Core Software

**Ollama:** install it and pull the model.

```bash
# Install Ollama via Homebrew
brew install --cask ollama

# Download the model
ollama pull llama3.1
```

**Python 3:** install a current Python 3 release. Check the minimum versions required by the current releases of `chromadb` and `sentence-transformers`, as these may be higher than 3.8.

```bash
brew install python3
```

**ffmpeg:** required by Whisper to read audio and video files.

```bash
brew install ffmpeg
```

**Local web server:** use MAMP or similar, or Python's built-in HTTP server.

### 4. Create a Virtual Environment

A virtual environment avoids `externally-managed-environment` errors and dependency conflicts.

```bash
python3 -m venv venv
source venv/bin/activate
```

```bash
pip install chromadb sentence-transformers fastapi uvicorn requests openai-whisper
```

### 5. Run the Pipeline

- **The model:** ensure Ollama is running in the background (the desktop app, or `ollama serve`).

- **Re-indexing (optional):** if new transcripts are added, rebuild the vector index.

  ```bash
  python3 build_index.py
  ```

- **The middleware:** start the API inside the virtual environment.

  ```bash
  python3 -m uvicorn backend:app --host localhost --port 8000
  ```

- **The frontend:** place the HTML file in your local server directory (for example, MAMP `htdocs`), or serve it with:

  ```bash
  python3 -m http.server 8888
  ```

### Offline Operation

Internet access is needed during first-time setup, when Whisper, Ollama and the embedding model are downloaded. After those downloads, the system can run without a connection. To enforce this, you can set the following before starting the backend:

```bash
export HF_HUB_OFFLINE=1
```

## Core Capabilities

- **Local data handling:** at runtime, media, databases and models all remain on the host machine. No queries or archive content are sent to third-party services, and the system is unaffected by platform changes, API limits or account deletions.
- **Prompt-level grounding:** the model is instructed to answer only from retrieved transcript excerpts and to state when the archive does not contain the answer. This supports, but does not guarantee, fidelity to the archive.
- **Timestamp-linked citations:** transcript timestamps are stored as metadata, so a citation can open the source video at the relevant point.

## Quick Start (Daily Usage / Post-Reboot)

If you restart your machine, follow these steps to bring the service back online.

### Step 1: Start the AI Service

Ensure the Ollama application is running in the background. Alternatively, in a terminal:

```bash
ollama serve
```

### Step 2: Launch the Backend API (Terminal Tab 2)

```bash
cd Sites/localhost/RAG
source venv/bin/activate
python3 -m uvicorn backend:app --host localhost --port 8000
```

### Step 3: Open the Interface

Ensure your local server (for example, MAMP) is active, then navigate to your local web address in your browser.

## Limitations

- **Transcription errors.** Whisper `small` output is unreviewed. Misheard names, dialect or period terminology will propagate into search results and answers. Manual review is advisable for scholarly or curatorial use.
- **Grounding is not guaranteed.** The "answer only from context" instruction can be ignored by the model, and answers should be checked against the cited source.
- **Partial citations.** The API retrieves three chunks but currently returns only the filename and start time of the top-ranked one. An answer may draw on other chunks that are not cited.
- **No relevance threshold.** The top three chunks are always retrieved, even if none is a good match, so weak matches can still be passed to the model.
- **Retrieval depth.** Fixed top-three retrieval may miss relevant material, particularly for questions spanning several recordings.
- **No formal evaluation.** Retrieval quality and answer accuracy have not been benchmarked against a reference question set.
- **Untested at scale.** The prototype has not been tested on large collections.
- **Permissive CORS.** The backend currently allows requests from any origin (`allow_origins=["*"]`). This is acceptable for local development but should be restricted before use on a shared network.

## Roadmap

1. Return citations for all retrieved chunks, not only the top-ranked one.
2. Apply a distance threshold to the ChromaDB results and return "the archive does not contain this information" without calling the model when no chunk is sufficiently close.
3. Restrict CORS to the frontend's origin (for example, `http://localhost:8888`) and remove `allow_credentials`.
4. Build a small evaluation set of questions with known answers and timestamps, and track retrieval accuracy over time.
5. Introduce a human review step for transcripts before indexing.
README.md
Displaying README.md.
