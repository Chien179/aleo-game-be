from src.lib.exception import BadRequest, Forbidden, NotFound, MethodNotAllow, ConflictError, InternalServer


class ErrReponse:
    @staticmethod
    def response(status_code, errors: any):
        if status_code == 400 or status_code == "Bad request":
            raise BadRequest(errors=errors)
        elif status_code == 403 or status_code == "Forbidden":
            raise Forbidden(errors=errors)
        elif status_code == 404 or status_code == "NotFound":
            raise NotFound(errors=errors)
        elif status_code == 405 or status_code == "Method not allow":
            raise MethodNotAllow()
        elif status_code == 409 or status_code == "Conflict":
            raise ConflictError()
        else:
            raise InternalServer(errors=errors)
