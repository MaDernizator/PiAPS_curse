from functools import wraps
from flask import request, session

def preserve_back_url(param_name="next", session_key="_back_url"):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            next_url = request.args.get(param_name)
            if next_url and next_url != request.path:
                session[session_key] = next_url
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
