from fastapi import Form

from typing import Annotated

def get_users() -> dict:
    users: dict[str, dict] = {
        "player1": {
            "id": 1,
            "password": "test123"
        },
        "player2": {
            "id": 2,
            "password": "test456"
        }
    }

    return users

def check_user(username: Annotated[str, Form()]) -> dict | None:
    users = get_users()

    return users.get(username)
