from pydantic import BaseModel as BM, ValidationError
from src.lib.exception import ValidationException
import json
from typing import Any

class BaseModel(BM):
    def __init__(__pydantic_self__, **data: Any) -> None:
        try:
            super(BaseModel, __pydantic_self__).__init__(**data)
        except ValidationError as pve:
            errors = {error["loc"][0]: error["msg"]
                      for error in json.loads(pve.json())}
            raise ValidationException(json.dumps(errors))