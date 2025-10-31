
from fastapi import HTTPException, status

class ReportNotFoundException(HTTPException):
    def __init__(self, detail: str = "Report not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class AgentExecutionException(HTTPException):
    def __init__(self, detail: str = "Agent execution failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
