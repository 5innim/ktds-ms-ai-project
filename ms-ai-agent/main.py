"""
Main entry point for the GitHub PR Impact Analyzer application.

This module sets up a FastAPI web server to receive GitHub webhooks and trigger
a LangGraph workflow for analyzing the impact of pull requests.
"""
import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi import Body
import httpx
import os

# --- Project Imports ---
from src.config import load_environment, set_github_token
from src.langgraph_workflow.graph import create_workflow

# --- Environment and Workflow Setup ---
# Load environment variables at the start
load_environment()

# Create the LangGraph workflow application
workflow_app = create_workflow()

# --- FastAPI Web Server ---
app = FastAPI(
    title="GitHub PR Impact Analyzer",
    description="Receives GitHub webhooks to analyze PR impact using LangGraph.",
)

is_rag_running: bool = False

@app.get("/rag/status")
async def get_rag_status():
    """
    Returns the current status of the RAG workflow.
    """
    return {"is_rag_running": is_rag_running}


@app.post("/webhook")
async def handle_webhook(request: Request):
    
    global is_rag_running

    event_type = request.headers.get('X-GitHub-Event')

    # Respond to ping events for webhook setup
    if event_type == 'ping':
        print("--- Received Ping Event ---")
        return {"status": "ping received"}

    # We are only interested in pull request events
    if event_type != 'pull_request':
        return {"status": f'Ignoring event: {event_type}'}

    try:
        payload_data = await request.json()
    except Exception as e:
        print(f"JSON parsing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Process only relevant pull request actions
    action = payload_data.get('action')
    if action not in ['opened', 'reopened', 'synchronize']:
        return {"status": f'Ignoring action: {action}'}

    # Initial state for the LangGraph workflow
    initial_state = {
        "repo_full_name": payload_data['repository']['full_name'],
        "pr_number": payload_data['pull_request']['number'],
        "pr_html_url": payload_data['pull_request']['html_url'],
    }

    # Asynchronously invoke the workflow
    try:
        # Note: LangGraph's invoke is synchronous. For a production system,
        # you might run this in a background task (e.g., with Celery or FastAPI's BackgroundTasks).
        is_rag_running = True
        final_state = workflow_app.invoke(initial_state)
        print("--- Workflow Finished ---")
        report = final_state.get("impact_report", "No report generated.")
        print("Final Report:", report)
        await sendMail("bjm222@naver.com", "report for PR", report)
        return {"status": "success", "report": report}
    except Exception as e:
        print(f"--- Workflow Error ---")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        is_rag_running = False
        print("--- Workflow Background Task Finished ---")
    
    
@app.post("/set-github-token")
async def api_set_github_token(payload: dict = Body(...)):
    """
    Set the global GITHUB_TOKEN at runtime.

    Expected JSON body: {"token": "ghp_..."}
    """
    token = payload.get("token")
    if not token or not isinstance(token, str):
        raise HTTPException(status_code=400, detail="Missing or invalid 'token' in request body")

    try:
        # persist_to_env=True will set os.environ['GITHUB_TOKEN'] as well
        set_github_token(token)
        return {"status": "success", "message": "GITHUB_TOKEN set"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def sendMail(to, subject, body):
    target_url = os.getenv("REPORT_TARGET_URL")
    
    if not target_url:
        print(f"--- [BG Task] REPORT_TARGET_URL not set. Skipping report POST. ---")
        return

    # 3. Preparar el payload y enviarlo usando httpx
    report_payload = {
        "to": to,
        "subject": subject,
        "body": body,
    }

    try:
        async with httpx.AsyncClient() as client:
            print(f"--- [BG Task] Sending report to {target_url} ---")
            response = await client.post(
                target_url,
                json=report_payload,
                headers={"Content-Type": "application/json"},
                timeout=15.0 # Añade un timeout
            )
            # Lanza un error si la respuesta es 4xx o 5xx
            response.raise_for_status() 
            print(f"--- [BG Task] Report sent successfully (Status: {response.status_code}) ---")
            
    except httpx.RequestError as e:
        print(f"--- [BG Task] !!! Error sending report to {target_url}: {e} !!! ---")
    except Exception as e:
        print(f"--- [BG Task] !!! An unexpected error occurred during report POST: {e} !!! ---")

@app.get("/")
def read_root():
    """
    Root endpoint for basic health checks.
    """
    return {"Hello": "World"}

# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)