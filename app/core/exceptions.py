class APIBaseError(Exception):
    """應用程式中所有自定義錯誤的基類"""
    def __init__(self, detail: str, name: str | None = None):
        self.detail = detail
        self.name = name or self.__class__.__name__
        super().__init__(self.detail)

class NotFoundError(APIBaseError):
    """db not found"""
    pass

# 業務異常 2：排程邏輯錯誤
class SchedulingError(APIBaseError):
    pass