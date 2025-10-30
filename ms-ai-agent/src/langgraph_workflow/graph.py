"""
Defines the LangGraph workflow for analyzing GitHub pull requests.
"""
import os
import re
import requests
from typing import TypedDict, List, Optional, Literal

from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import PythonCodeTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import GithubFileLoader
from langchain_core.documents import Document

from src.util.parser import java_parser

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
        language: The primary language of the repository ('python' or 'java').
    """
    repo_full_name: str
    pr_number: int
    pr_html_url: str
    pr_files: Optional[List[dict]] = None
    repo_docs: Optional[List[Document]] = None
    chunks: Optional[List[Document]] = None
    vector_store: Optional[object] = None
    impact_report: Optional[str] = None
    error: Optional[str] = None
    language: Optional[Literal["python", "java"]] = None
    impact_context: Optional[str] = None


# --- Graph Nodes ---
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
        response.raise_for_status()
        files = response.json()
        pr_files = [
            {"filename": file["filename"], "patch": file["patch"]}
            for file in files
        ]
        
        print(f"Found {len(pr_files)} changed files in PR #{pr_number}.")
        
        state["pr_files"] = pr_files
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PR files: {e}")
        state["error"] = f"Failed to fetch PR files: {e}"

    return state

def load_repository(state: GraphState) -> GraphState:
    """Loads all relevant files (.py, .java) from the repository."""
    print("--- (2) Loading Repository Files ---")
    if state.get("error"):
        return state

    repo_full_name = state["repo_full_name"]
    github_token = os.environ.get("GITHUB_TOKEN")

    try:
        loader = GithubFileLoader(
            repo=repo_full_name,
            access_token=github_token,
            github_api_url="https://api.github.com",
            branch="main",
            file_filter=lambda file_path: (file_path.endswith(".py") or file_path.endswith(".java")) and \
                                        all(part not in file_path for part in ["__pycache__", ".venv", ".git", "target"])
        )
        repo_docs = loader.load()
        print(f"Loaded {len(repo_docs)} documents from the repo.")
        state["repo_docs"] = repo_docs
    except Exception as e:
        print(f"Error loading repository: {e}")
        state["error"] = f"Failed to load repository: {e}"
    
    return state

def determine_language(state: GraphState) -> GraphState:
    """Determines the primary language of the PR based on file extensions."""
    print("--- (2a) Determining Language ---")
    if state.get("error") or not state.get("repo_docs"):
        return state

    if any(doc.metadata.get("source", "").endswith(".java") for doc in state["repo_docs"]):
        print("Language is Java")
        state["language"] = "java"
    else:
        print("Language is Python")
        state["language"] = "python"
    return state

def chunk_and_embed_python(state: GraphState) -> GraphState:
    """Chunks Python documents and creates a vector store."""
    print("--- (3a) Chunking and Embedding Python ---")
    repo_docs = state["repo_docs"]
    
    try:
        text_splitter = PythonCodeTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(repo_docs)
        print(f"Created {len(chunks)} code chunks.")

        embeddings = OpenAIEmbeddings(disallowed_special=())
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        state["chunks"] = chunks
        state["vector_store"] = vector_store
        print("Successfully created vector store for Python.")
    except Exception as e:
        print(f"Error during Python chunking and embedding: {e}")
        state["error"] = f"Failed to chunk and embed Python: {e}"
    return state

def chunk_and_embed_java(state: GraphState) -> GraphState:
    """Chunks Java documents and creates a vector store."""
    print("--- (3b) Chunking and Embedding Java ---")
    if state.get("error") or not state.get("repo_docs"):
        return state

    repo_docs = state["repo_docs"]
    
    try:
        all_chunks = []
        for doc in repo_docs:
            print(f"Processing doc: {doc.metadata.get('source')}")
            if doc.metadata.get('source', '').endswith(".java"):
                chunks = java_parser.get_class_and_method_chunks(doc)
                all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} code chunks for Java.")

        embeddings = OpenAIEmbeddings(disallowed_special=())
        vector_store = FAISS.from_documents(all_chunks, embeddings)
        
        state["chunks"] = all_chunks
        state["vector_store"] = vector_store
        print("Successfully created vector store for Java.")

    except Exception as e:
        print(f"Error during Java chunking and embedding: {e}")
        state["error"] = f"Failed to chunk and embed Java: {e}"

    return state

def find_usages_python(state: GraphState) -> GraphState:
    """Identifies changed Python symbols and finds their usages."""
    print("--- (4a) Finding Usages of Changed Python Code ---")
    pr_files = state["pr_files"]
    vector_store = state["vector_store"]
    impact_context = []

    for file in pr_files:
        patch = file.get("patch", "")
        if not patch or not file.get("filename", "").endswith(".py"):
            continue

        changed_symbols = re.findall(r"(?:class|def)\s+([\w_]+)", patch)
        
        for symbol in set(changed_symbols):
            print(f"Analyzing symbol: {symbol} in file {file['filename']}")
            retriever = vector_store.as_retriever()
            relevant_docs = retriever.get_relevant_documents(symbol)
            
            usage_snippets = [
                f"- Usage in `{doc.metadata['source']}`:\n```python\n{doc.page_content}\n```"
                for doc in relevant_docs
                if f"def {symbol}" not in doc.page_content and f"class {symbol}" not in doc.page_content
            ]
            
            context = (
                f"Change in `{file['filename']}` related to symbol `{symbol}`:\n"
                f"**Diff:**\n```diff\n{patch}\n```\n"
                f"**Potential Usages:**\n" + "\n".join(usage_snippets)
            )
            impact_context.append(context)

    state["impact_context"] = "\n\n---\n\n".join(impact_context)
    return state

def find_usages_java(state: GraphState) -> GraphState:
    """Identifies changed Java symbols and finds their usages."""
    print("--- (4b) Finding Usages of Changed Java Code ---")
    if state.get("error") or not state.get("vector_store"):
        return state

    pr_files = state["pr_files"]
    repo_docs_map = {doc.metadata["path"]: doc.page_content for doc in state["repo_docs"]}
    vector_store = state["vector_store"]
    impact_context = []

    for file in pr_files:
        filename = file.get("filename")
        patch = file.get("patch", "")
        if not patch or not filename or not filename.endswith(".java"):
            continue

        file_content = repo_docs_map.get(filename)
        if not file_content:
            continue

        changed_symbols = java_parser.get_changed_symbols_from_patch(patch, file_content)

        for symbol in set(changed_symbols):
            print(f"Analyzing symbol: {symbol} in file {filename}")
            retriever = vector_store.as_retriever()
            relevant_docs = retriever.get_relevant_documents(symbol)
            
            usage_snippets = [
                f"- Usage in `{doc.metadata['source']}` (Line {doc.metadata['start_line']}):\n```java\n{doc.page_content}\n```"
                for doc in relevant_docs
                if symbol not in doc.metadata.get("symbol_name", "") # Basic check to avoid self-reference
            ]
            
            context = (
                f"Change in `{filename}` related to symbol `{symbol}`:\n"
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
            ("system", "You are a senior software engineer..."), # Same prompt
            ("human", "Please generate an impact analysis report for... {pr_url}... {impact_context}"),
        ]
    )
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    chain = prompt_template | llm

    try:
        report = chain.invoke({"pr_url": pr_url, "impact_context": impact_context})
        state["impact_report"] = report.content
        print("Successfully generated impact report.")
    except Exception as e:
        print(f"Error generating report: {e}")
        state["error"] = f"Failed to generate report: {e}"
    return state

def route_by_language(state: GraphState) -> Literal["chunk_and_embed_java", "chunk_and_embed_python"]:
    """Routes to the appropriate chunking node based on the detected language."""
    if state["language"] == "java":
        return "chunk_and_embed_java"
    else:
        return "chunk_and_embed_python"

# --- Graph Workflow Definition ---
def create_workflow():
    """Creates and configures the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    workflow.add_node("get_pr_details", get_pr_details)
    workflow.add_node("load_repository", load_repository)
    workflow.add_node("determine_language", determine_language)
    workflow.add_node("chunk_and_embed_python", chunk_and_embed_python)
    workflow.add_node("chunk_and_embed_java", chunk_and_embed_java)
    workflow.add_node("find_usages_python", find_usages_python)
    workflow.add_node("find_usages_java", find_usages_java)
    workflow.add_node("generate_report", generate_report)

    workflow.set_entry_point("get_pr_details")
    workflow.add_edge("get_pr_details", "load_repository")
    workflow.add_edge("load_repository", "determine_language")

    workflow.add_conditional_edges(
        "determine_language",
        route_by_language,
        {
            "chunk_and_embed_java": "chunk_and_embed_java",
            "chunk_and_embed_python": "chunk_and_embed_python",
        },
    )

    workflow.add_edge("chunk_and_embed_python", "find_usages_python")
    workflow.add_edge("chunk_and_embed_java", "find_usages_java")

    workflow.add_edge("find_usages_python", "generate_report")
    workflow.add_edge("find_usages_java", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()
