
import os
from typing import TypedDict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from langgraph.graph import StateGraph, END
import uvicorn
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import PythonCodeTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import GithubFileLoader
from pydantic import BaseModel

# --- Environment Setup ---
from dotenv import load_dotenv

load_dotenv()

# Ensure necessary environment variables are set
assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY environment variable not set."
assert os.environ.get("GITHUB_TOKEN"), "GITHUB_TOKEN environment variable not set."


# --- Pydantic Models for Webhook ---
class PullRequest(BaseModel):
    number: int
    html_url: str

class Repository(BaseModel):
    full_name: str

class WebhookPayload(BaseModel):
    action: str
    pull_request: PullRequest
    repository: Repository


# --- LangGraph State ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        repo_full_name: The full name of the repository (e.g., "owner/repo").
        pr_number: The pull request number.
        pr_html_url: The URL of the pull request.
        pr_files: A list of files changed in the PR.
        repo_docs: Documents loaded from the repository's base branch.
        chunks: Code chunks created from the repo documents.
        vector_store: The vector store containing embedded chunks.
        impact_report: The final impact analysis report.
        error: Any error messages that occur during the process.
    """
    repo_full_name: str
    pr_number: int
    pr_html_url: str
    pr_files: Optional[List[dict]] = None
    repo_docs: Optional[List] = None
    chunks: Optional[List] = None
    vector_store: Optional[object] = None
    impact_report: Optional[str] = None
    error: Optional[str] = None


# --- Graph Nodes (to be implemented) ---
import requests

def get_pr_details(state: GraphState) -> GraphState:
    """Fetches the list of changed files from a GitHub pull request."""
    print("--- (1) Fetching PR Details ---")
    repo_full_name = state["repo_full_name"]
    pr_number = state["pr_number"]
    github_token = os.environ.get("GITHUB_TOKEN")
    
    api_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        files = response.json()
        
        # We only need the filename and patch for our analysis
        pr_files = [
            {"filename": file["filename"], "patch": file.get("patch")}
            for file in files
        ]
        
        print(f"Found {len(pr_files)} changed files in PR #{pr_number}.")
        state["pr_files"] = pr_files
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PR files: {e}")
        state["error"] = f"Failed to fetch PR files: {e}"

    return state

def load_repository(state: GraphState) -> GraphState:
    """Loads all python files from the repository using GithubFileLoader."""
    print("--- (2) Loading Repository Files ---")
    if state.get("error"):  # If a previous step failed, skip
        return state

    repo_full_name = state["repo_full_name"]
    github_token = os.environ.get("GITHUB_TOKEN")

    try:
        # For this example, we assume the PR is against the main branch.
        # A real implementation would need to get the base branch from the webhook.
        loader = GithubFileLoader(
            repo=repo_full_name,
            access_token=github_token,
            github_api_url="https://api.github.com",
            branch="main",  # Assuming base branch is main
            file_filter=lambda file_path: file_path.endswith(".py") and 
                                        all(part not in file_path for part in ["__pycache__", ".venv", ".git"])
        )
        repo_docs = loader.load()
        print(f"Loaded {len(repo_docs)} documents from the repo.")
        state["repo_docs"] = repo_docs
    except Exception as e:
        print(f"Error loading repository: {e}")
        state["error"] = f"Failed to load repository: {e}"
    
    return state

def chunk_and_embed(state: GraphState) -> GraphState:
    """Chunks the documents and creates a vector store."""
    print("--- (3) Chunking and Embedding ---")
    if state.get("error") or not state.get("repo_docs"):
        return state

    repo_docs = state["repo_docs"]
    
    try:
        # Split documents into chunks based on class and function definitions
        text_splitter = PythonCodeTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(repo_docs)
        
        print(f"Created {len(chunks)} code chunks.")

        # Create embeddings and build the vector store
        embeddings = OpenAIEmbeddings(disallowed_special=())
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        state["chunks"] = chunks
        state["vector_store"] = vector_store
        print("Successfully created vector store.")

    except Exception as e:
        print(f"Error during chunking and embedding: {e}")
        state["error"] = f"Failed to chunk and embed: {e}"

    return state

import re

def find_usages(state: GraphState) -> GraphState:
    """Identifies changed symbols and finds their usages in the codebase."""
    print("--- (4) Finding Usages of Changed Code ---")
    if state.get("error") or not state.get("vector_store"):
        return state

    pr_files = state["pr_files"]
    vector_store = state["vector_store"]
    impact_context = []

    for file in pr_files:
        patch = file.get("patch", "")
        if not patch:
            continue

        # A simple regex to find function and class names from the patch's hunk headers
        # Example hunk header: @@ -15,6 +15,7 @@ class MyClass:
        changed_symbols = re.findall(r"(?:class|def)\s+([\w_]+)", patch)
        
        if not changed_symbols:
            continue

        # For each changed symbol, find its usages
        for symbol in set(changed_symbols):
            print(f"Analyzing symbol: {symbol} in file {file['filename']}")
            # Find relevant chunks from the vector store
            retriever = vector_store.as_retriever()
            relevant_docs = retriever.get_relevant_documents(symbol)
            
            usage_snippets = []
            for doc in relevant_docs:
                # Avoid showing the definition itself, focus on usages
                if f"def {symbol}" not in doc.page_content and f"class {symbol}" not in doc.page_content:
                    usage_snippets.append(
                        f"- Usage in `{doc.metadata['source']}`:\n```python\n{doc.page_content}\n```"
                    )
            
            context = (
                f"Change in `{file['filename']}` related to symbol `{symbol}`:\n"
                f"**Diff:**\n```diff\n{patch}\n```\n"
                f"**Potential Usages:**\n" + "\n".join(usage_snippets)
            )
            impact_context.append(context)

    state["impact_context"] = "\n\n---\n\n".join(impact_context)
    return state

def generate_report(state: GraphState) -> GraphState:
    """Generates a final impact analysis report using the LLM."""
    print("--- (5) Generating Impact Report ---")
    if state.get("error") or not state.get("impact_context"):
        state["impact_report"] = "Could not generate a report due to earlier errors or no impact context found."
        return state

    pr_url = state["pr_html_url"]
    impact_context = state["impact_context"]

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a senior software engineer providing a code impact analysis. "
                "Your goal is to help the PR author and reviewers understand the potential consequences of the changes. "
                "Analyze the provided context, which includes diffs and potential usages of the changed code. "
                "Structure your report with a summary, a risk assessment (High/Medium/Low), and concrete test suggestions."
            ),
            (
                "human",
                "Please generate an impact analysis report for the following pull request: {pr_url}\n\n"
                "Here is the context of the changes and their potential usages:\n\n"
                "{impact_context}"
            ),
        ]
    )

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    chain = prompt_template | llm

    try:
        report = chain.invoke({"pr_url": pr_url, "impact_context": impact_context})
        state["impact_report"] = report.content
        print("Successfully generated impact report.")
    except Exception as e:
        print(f"Error generating report: {e}")
        state["error"] = f"Failed to generate report: {e}"
        state["impact_report"] = "Failed to generate report."

    return state


# --- Graph Workflow Definition ---
workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("get_pr_details", get_pr_details)
workflow.add_node("load_repository", load_repository)
workflow.add_node("chunk_and_embed", chunk_and_embed)
workflow.add_node("find_usages", find_usages)
workflow.add_node("generate_report", generate_report)

# Build the graph
workflow.set_entry_point("get_pr_details")
workflow.add_edge("get_pr_details", "load_repository")
workflow.add_edge("load_repository", "chunk_and_embed")
workflow.add_edge("chunk_and_embed", "find_usages")
workflow.add_edge("find_usages", "generate_report")
workflow.add_edge("generate_report", END)

# Compile the app
app = workflow.compile()


# --- FastAPI Web Server ---
fastapi_app = FastAPI(
    title="GitHub PR Impact Analyzer",
    description="Receives GitHub webhooks to analyze PR impact using LangGraph.",
)

@fastapi_app.post("/webhook")
async def handle_webhook(payload: WebhookPayload):
    if payload.action not in ["opened", "reopened", "synchronize"]:
        return {"status": "action ignored"}

    print(f"--- Received PR #{payload.pull_request.number} for repo {payload.repository.full_name} ---")

    # Initial state for the graph
    initial_state = {
        "repo_full_name": payload.repository.full_name,
        "pr_number": payload.pull_request.number,
        "pr_html_url": payload.pull_request.html_url,
    }

    # Asynchronously run the graph
    # Note: In a real-world scenario, you'd handle this in the background
    # to avoid long-running HTTP requests.
    try:
        # The `app` here is the compiled LangGraph
        final_state = app.invoke(initial_state)
        print("--- Workflow Finished ---")
        print("Final Report:", final_state.get("impact_report", "No report generated."))
        return {"status": "success", "report": final_state.get("impact_report")}
    except Exception as e:
        print(f"--- Workflow Error ---")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
