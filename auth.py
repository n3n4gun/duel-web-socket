import os
import jwt

from datetime import datetime, timedelta, timezone

def create_access_token(user_id: int) -> str:
    current_time = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'iat': current_time,
        'exp': current_time + timedelta(minutes = 30)
    }

    access_token = jwt.encode(
        payload = payload,
        key = os.getenv('SECRET_KEY'),
        algorithm = os.getenv('ALGORITHM')
    )

    return access_token

def verify_access_token(access_token: str) -> int | None:
    try:
        decoded_token = jwt.decode(
            jwt = access_token,
            key = os.getenv('SECRET_KEY'),
            algorithms = [os.getenv('ALGORITHM')],
            options = {
                'require': ['sub', 'iat', 'exp']
            }
        )

        return int(decoded_token['sub'])

    except (ValueError, jwt.InvalidTokenError):
        return None
