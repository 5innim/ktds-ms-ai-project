from langchain_community.document_loaders import GithubFileLoader

def load_project(access_token, repo_uri, branch):

    ACCESS_TOKEN = "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"
    #"5innim/okky_copy_backend_project"
    # main
    loader = GithubFileLoader(
        repo=repo_uri,  
        branch=branch,  
        access_token=access_token,
        github_api_url="https://api.github.com",
        file_filter=lambda file_path: file_path.endswith(
            ".java"
        ) or file_path.endswith(
            ".xml"
        ),  
    )
    
    return loader.load()

