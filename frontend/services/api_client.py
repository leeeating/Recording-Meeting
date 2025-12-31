import requests

from app.models.schemas import MeetingCreateSchema


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        # 確保 base_url 結尾沒有 /
        self.base_url = base_url.rstrip("/")
        self.timeout = 10

    def create_meeting(self, data: MeetingCreateSchema):
        """專門處理「創建會議」的網路通訊"""
        url = f"{self.base_url}/meeting"  # 配合後端路由調整有無斜線

        # 💡 重要：處理 datetime 序列化問題
        # model_dump(mode='json') 會自動把 datetime 轉成 ISO 格式字串
        payload = data.model_dump(mode="json")

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)

            # 如果後端回報錯誤 (如 422 格式錯誤)，印出詳細訊息方便除錯
            if response.status_code == 422:
                print(f"DEBUG: FastAPI 驗證失敗 -> {response.text}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # 重新封裝成更易讀的錯誤訊息給 Worker 抓取
            raise Exception(f"API 連線異常: {str(e)}")

    def get_all_tasks(self):
        """專門處理「獲取所有會議」的網路通訊"""
        url = f"{self.base_url}/meeting"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def update_meeting(self, meeting_id: str, data: MeetingCreateSchema):
        """專門處理「更新會議」的網路通訊"""
        pass
