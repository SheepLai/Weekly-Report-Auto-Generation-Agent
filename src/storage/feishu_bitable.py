"""
飞书多维表格存储模块

提供飞书多维表格的创建、读写操作能力
"""
import requests
from functools import wraps
from cozeloop.decorator import observe
from coze_workload_identity import Client


def get_access_token() -> str:
    """
    获取飞书多维表格的租户访问令牌
    """
    client = Client()
    access_token = client.get_integration_credential("integration-feishu-base")
    return access_token


def require_token(func):
    """装饰器：确保访问令牌可用"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.access_token = get_access_token()
        if not self.access_token:
            raise ValueError("Access token is not available")
        return func(self, *args, **kwargs)
    return wrapper


class FeishuBitable:
    """
    飞书多维表格 HTTP 客户端
    """
    def __init__(self, base_url: str = "https://open.larkoffice.com/open-apis", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token = get_access_token()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "Content-Type": "application/json; charset=utf-8",
        }

    @observe
    def _request(self, method: str, path: str, params: dict = None, json: dict = None) -> dict:
        try:
            url = f"{self.base_url}{path}"
            resp = requests.request(
                method, url,
                headers=self._headers(),
                params=params,
                json=json,
                timeout=self.timeout
            )
            resp_data = resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"FeishuBitable API request error: {e}")

        if resp_data.get("code") != 0:
            raise Exception(f"FeishuBitable API error: {resp_data}")

        return resp_data

    @require_token
    def create_base(self, name: str = None, folder_token: str = None, time_zone: str = None) -> dict:
        """
        创建多维表格 Base
        """
        body = {}
        if name is not None:
            body["name"] = name
        if folder_token is not None:
            body["folder_token"] = folder_token
        if time_zone is not None:
            body["time_zone"] = time_zone
        return self._request("POST", "/bitable/v1/apps", json=body)

    @require_token
    def get_base_info(self, app_token: str) -> dict:
        """
        获取 Base 信息
        """
        return self._request("GET", f"/bitable/v1/apps/{app_token}")

    @require_token
    def list_tables(self, app_token: str, page_token: str = None, page_size: int = None) -> dict:
        """
        列出 Base 下所有数据表
        """
        params = {}
        if page_token is not None:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size
        return self._request("GET", f"/bitable/v1/apps/{app_token}/tables", params=params)

    @require_token
    def create_table(self, app_token: str, table_name: str, fields: list = None) -> dict:
        """
        创建数据表
        """
        body = {"table_name": table_name}
        if fields is not None:
            body["fields"] = fields
        return self._request("POST", f"/bitable/v1/apps/{app_token}/tables", json=body)

    @require_token
    def add_records(self, app_token: str, table_id: str, records: list, user_id_type: str = None) -> dict:
        """
        批量新增记录
        """
        params = {}
        if user_id_type is not None:
            params["user_id_type"] = user_id_type

        body = {"records": records}
        return self._request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create", params=params, json=body)

    @require_token
    def search_record(
        self,
        app_token: str,
        table_id: str,
        filter: dict = None,
        page_token: str = None,
        page_size: int = None,
    ) -> dict:
        """
        条件查询记录
        """
        params = {}
        if page_token is not None:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size

        body = {}
        if filter is not None:
            body["filter"] = filter

        return self._request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search", params=params, json=body)
