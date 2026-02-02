from fastapi import HTTPException, status


class UserException(HTTPException):
    def __init__(self, message) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class TaskNotFoundException(HTTPException):
    def __init__(self, task_id=None) -> None:
        detail = f"Task {task_id} not found" if task_id else "Task not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AlreadyExistingIDException(HTTPException):
    def __init__(self, id) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f"ID {id} already used")


class AuthenticationException(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
