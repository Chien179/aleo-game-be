from functools import wraps
from typing import Optional, Type
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import UploadFile
from src.lib.exception import BadRequest, BaseException as BE
from src.lib.authentication import Authorization
from src.lib.logger import logger
from pydantic import BaseModel
from src.lib.enum import APIResponseCode

import traceback
import asyncio
import json
import tracemalloc

def executor(
    login_require: Optional[Authorization] = None,
    query_params: Optional[Type[BaseModel]] = None,
    form_data: Optional[Type[BaseModel]] = None,
    path_params: Optional[Type[BaseModel]] = None,
    trace_error: bool=True,
    allow_roles = ['ALL']
):
    def _internal(f):
        @wraps(f)
        async def decorated(*args, **kwargs):
            tracemalloc.start()

            _res = {
                'data': '',
                'msg': '',
                'code': '',
                'errors': {},
            }
            try:
                _request: Request = args[1]
                _self = args[0]

                _kwargs = _request.state._state
                _kwargs['self'] = _self

                if login_require:
                    if asyncio.iscoroutinefunction(login_require.validate):
                        _payload = await login_require.validate(_request)
                    else:
                        _payload = login_require.validate(_request)                       
                    _kwargs['user'] = _payload

                if len(allow_roles) > 0 and 'ALL' not in allow_roles:
                    _role = _kwargs['user'].get('role')
                    if _role not in allow_roles:
                        raise BadRequest(
                            msg='Permission denied', code=APIResponseCode.FORBIDDEN.value["code"])

                if query_params:
                    _params_data = _request.query_params._dict
                    try:
                        _prams = query_params(**_params_data)
                        
                        _kwargs['query_params'] = json.loads(_prams.model_dump_json())
                    except Exception as e:
                        raise BadRequest(errors=json.loads(e.json()), 
                                         code=APIResponseCode.FAIL_FORMAT.value["code"],
                                         msg=APIResponseCode.FAIL_FORMAT.value["detail"])
                    
                if path_params:
                    _path_data = _request.path_params
                    try:
                        _prams = path_params(**_path_data)
                        _kwargs['path_params'] = json.loads(_prams.model_dump_json())
                    except Exception as e:
                        raise BadRequest(errors=json.loads(
                            e.json()), code=APIResponseCode.FAIL_FORMAT.value["code"],
                            msg=APIResponseCode.FAIL_FORMAT.value["detail"])

                if form_data:
                    _content_type = _request.headers.get('content-type')
                    if _content_type is None:
                        raise BadRequest(errors="data is required", code=APIResponseCode.FAIL_FORMAT.value["code"],
                                         msg=APIResponseCode.FAIL_FORMAT.value["detail"])

                    if _content_type == 'application/json':
                        try:
                            _form_data = await _request.json()
                            _data = form_data(**_form_data)
                            _kwargs['form_data'] =json.loads(_data.model_dump_json())
                        except Exception as e:
                            raise BadRequest(errors=json.loads(
                                e.json()), code=APIResponseCode.FAIL_FORMAT.value["code"],
                                msg=APIResponseCode.FAIL_FORMAT.value["detail"])

                    elif _content_type.startswith('multipart/form-data'):
                        async with _request.form() as form:
                            _data = {}
                            for k, v in form._dict.items():
                                if isinstance(v, UploadFile):
                                    _data[k] = await v.read()
                                else:
                                    _data[k] = v
                            try:
                                _data = form_data(**_data)
                                _kwargs['form_data'] = json.loads(_data.model_dump_json())
                            except Exception as e:
                                raise BadRequest(errors=json.loads(
                                    e.json()), code=APIResponseCode.FAIL_FORMAT.value["code"],
                                    msg=APIResponseCode.FAIL_FORMAT.value["detail"])
                function_var = {}
                for var_name in f.__code__.co_varnames:
                    if _kwargs.get(var_name):
                        function_var[var_name] = _kwargs[var_name]
                if asyncio.iscoroutinefunction(f):
                    _response = await f(**function_var)
                else:
                    _response = f(**function_var)
                if isinstance(_response, Response):
                    return _response
                else:
                    _res['data'] = _response
                    _res['code'] = APIResponseCode.SUCCESS_CODE.value["code"]
                return Response(
                    content=json.dumps(_res),
                    status_code=200,
                    headers={'Content-type': 'application/json'}
                )
            except Exception as e:
                if trace_error and not isinstance(e, BE):
                    traceback.print_exc()
                _exc_header = {'Content-type': 'application/json'}
                _status = 400
                if isinstance(e, BE):
                    _res['errors'] = e.errors
                    _res['msg'] = e.msg
                    _res['code'] = e.code
                    _status = e.status
                else:
                    _res['errors'] = str(e)
                    _status = 400
                    _res['code'] = APIResponseCode.NOT_FOUND.value["code"]
                tracemalloc.stop()
                return Response(json.dumps(_res), status_code=_status, headers=_exc_header)
        return decorated
    return _internal
