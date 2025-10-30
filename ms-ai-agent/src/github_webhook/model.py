"""
Pydantic models for the GitHub webhook payload.
"""
from pydantic import BaseModel

class PullRequest(BaseModel):
    number: int
    html_url: str

class Repository(BaseModel):
    full_name: str

class WebhookPayload(BaseModel):
    action: str
    pull_request: PullRequest
    repository: Repository
