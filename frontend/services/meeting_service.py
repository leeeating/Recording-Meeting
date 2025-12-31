from frontend.services import ApiWorker


class MeetingService:
    def __init__(self, api_client):
        self.api_client = api_client

    def save_meeting(self, meeting_id, meeting_data, on_success, on_error):
        """
        根據有無 meeting_id 決定呼叫建立或更新。
        回傳 worker 供 View 層保持引用。
        """
        if meeting_id:
            # 修改模式
            worker = ApiWorker(self.api_client.update_meeting, meeting_id, meeting_data)
        else:
            # 新增模式
            worker = ApiWorker(self.api_client.create_meeting, meeting_data)

        worker.success.connect(on_success)
        worker.error.connect(on_error)
        worker.start()
        return worker
