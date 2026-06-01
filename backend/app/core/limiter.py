from slowapi import Limiter
from slowapi.util import get_remote_address

# Central limiter instance used across the app
limiter = Limiter(key_func=get_remote_address)
