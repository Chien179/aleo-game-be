
from src.lib.enum import APIResponseCode

class BaseException(Exception):

    def __init__(self, msg="", code=APIResponseCode.ERROR_NOT_IDENTIFIED.value["code"], *args: object) -> None:
        super().__init__(*args)
        self.msg = msg
        self.status = 400
        self.code = code
        self.errors = {}

class ValidationException(Exception):
    def __init__(self, msg="", *args: object) -> None:
        super().__init__(*args) 
        self.msg = msg

    def json(self):
        return self.msg

class BadRequest(BaseException):
    def __init__(self, msg="Bad request", code=APIResponseCode.ERROR_NOT_IDENTIFIED.value["code"], errors={}, *args: object) -> None:
        super().__init__(msg, code, *args)
        self.errors = errors

class Forbidden(BaseException):
    def __init__(self, msg="Forbidden", code=APIResponseCode.FORBIDDEN.value["code"], errors={}, *args: object) -> None:
        super().__init__(msg, code, *args)
        self.errors = errors
        self.status = 403

class NotFound(BaseException):
    def __init__(self, msg="NotFound", code=APIResponseCode.ERROR_NOT_IDENTIFIED.value["code"], errors={}, *args: object) -> None:
        super().__init__(msg, *args)
        self.error = errors
        self.status = 404

class MethodNotAllow(BaseException):
    def __init__(self, msg="Method not allow", code=APIResponseCode.ERROR_NOT_IDENTIFIED.value["code"],*args: object) -> None:
        super().__init__(msg, code="",*args)
        self.status = 405

class ConflictError(BaseException):
    def __init__(self, msg="Conflict", code=APIResponseCode.ERROR_NOT_IDENTIFIED.value["code"], *args: object) -> None:
        super().__init__(msg, code, *args)
        self.status = 409

class InternalServer(BaseException):
    def __init__(self, msg="Internal server error", errors={}, code=APIResponseCode.INTERNAL_SERVER.value["code"], *args: object) -> None:
        super().__init__(msg, code, *args)
        self.errors = errors
        self.status = 500