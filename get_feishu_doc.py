#!/usr/bin/env python
"""
获取飞书文档内容
"""
import requests
from coze_workload_identity import Client

def get_access_token():
    """获取飞书 access_token"""
    client = Client()
    # 尝试获取飞书基础集的 access token
    try:
        access_token = client.get_integration_credential("integration-feishu-base")
        return access_token
    except:
        # 如果获取失败，返回 None
        return None

def get_docx_content(doc_token: str, access_token: str) -> dict:
    """
    获取飞书云文档内容
    文档 API: GET /docx/v1/documents/{document_id}/raw_content
    """
    base_url = "https://open.feishu.cn/open-apis"
    url = f"{base_url}/docx/v1/documents/{doc_token}/raw_content"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp_data = resp.json()
        print(f"Response status: {resp.status_code}")
        print(f"Response data: {resp_data}")
        return resp_data
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {"error": str(e)}

def get_docx_meta(doc_token: str, access_token: str) -> dict:
    """
    获取飞书云文档元信息
    文档 API: GET /docx/v1/documents/{document_id}
    """
    base_url = "https://open.feishu.cn/open-apis"
    url = f"{base_url}/docx/v1/documents/{doc_token}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp_data = resp.json()
        print(f"Meta Response status: {resp.status_code}")
        print(f"Meta Response data: {resp_data}")
        return resp_data
    except requests.exceptions.RequestException as e:
        print(f"Meta Request error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # 文档 token
    doc_token = "Pc4tdSsD5o7WyXx8EPwccdN2nUd"
    
    # 获取 access token
    access_token = get_access_token()
    print(f"Access token: {access_token}")
    
    if access_token:
        # 先获取文档元信息
        print("\n=== 获取文档元信息 ===")
        meta = get_docx_meta(doc_token, access_token)
        
        # 再获取文档内容
        print("\n=== 获取文档内容 ===")
        content = get_docx_content(doc_token, access_token)
    else:
        print("Failed to get access token")
