import os
import json
import requests

def trigger_workflow(session_id: str, service: str, workflow_data: dict):
    """Trigger GitHub Actions workflow via API"""
    
    github_token = os.environ.get('GITHUB_TOKEN')
    github_repo = os.environ.get('GITHUB_REPO')  # format: username/repo
    
    if not github_token or not github_repo:
        print("GitHub credentials not configured")
        return False
    
    url = f"https://api.github.com/repos/{github_repo}/actions/workflows/upload.yml/dispatches"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {github_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'ref': 'main',
        'inputs': {
            'session_id': session_id,
            'service': service,
            'workflow_data': json.dumps(workflow_data)
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            print(f"Workflow triggered successfully for session: {session_id}")
            return True
        else:
            print(f"Failed to trigger workflow: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"Error triggering workflow: {e}")
        return False

if __name__ == '__main__':
    # Test trigger
    test_data = {
        'session_id': 'test123',
        'service': 'pixeldrain',
        'files': [],
        'user_id': '123456',
        'chat_id': 123456,
        'message_id': 1
    }
    
    trigger_workflow('test123', 'pixeldrain', test_data)
