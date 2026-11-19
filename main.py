import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, Depends, Response, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocketState

from dotenv import load_dotenv
from typing import Annotated

from users import check_user
from managers.connectionManager import connection_manager
from auth import create_access_token, verify_access_token

load_dotenv()

duel_app = FastAPI()
templates = Jinja2Templates(directory = 'templates')

if os.getenv('ALLOWED_ORIGINS', None) is None:
    raise RuntimeError(
        'Required environment variable ALLOWED_ORIGINS is not set'
    )

ALLOWED_ORIGINS = {origin for origin in os.getenv('ALLOWED_ORIGINS').split(',')}

@duel_app.get('/')
async def return_index(
    request: Request
):
    access_token = request.cookies.get('access_token')

    if not access_token or verify_access_token(access_token) is None:
        return RedirectResponse(
            url = '/login',
            status_code = status.HTTP_303_SEE_OTHER
        )

    return templates.TemplateResponse(
        request = request,
        name = 'index.html'
    )

@duel_app.get('/login')
async def retur_login_page(
    request: Request
):
    return templates.TemplateResponse(
        request = request,
        name = 'login.html'
    )

@duel_app.post('/login')
async def login(
    password: Annotated[str, Form()],
    current_user: Annotated[dict | None, Depends(check_user)],
    response: Response
):
    if not current_user or password != current_user['password']:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Invalid credentials'
        )

    access_token = create_access_token(current_user['id'])
    response.set_cookie(
        key = 'access_token',
        value = access_token,
        httponly = True,
        secure = False,
        samesite = 'lax',
        max_age = 1800,
        path = '/'
    )
    
    return {'status': 'ok'}

@duel_app.websocket('/ws/chat')
async def send__message(
    websocket: WebSocket
):
    connected = False

    user_access_token = websocket.cookies.get('access_token')
    origin = websocket.headers.get('origin')

    if origin not in ALLOWED_ORIGINS or not user_access_token:
        await websocket.close(code = 1008)
        return

    user_id = verify_access_token(user_access_token)

    if user_id is None:
        await websocket.close(code = 1008)
        return

    try:
        connected = await connection_manager.connect(user_id, websocket)

        if not connected:
            return
        
        await connection_manager.broadcast(
            {
                'type': 'system',
                'text': 'Новый клиент подключился'
            }
        )

        await websocket.send_json(
            data = {
                'type': 'system',
                'text': 'Добро пожаловать в чат!'
            }
        )

        while True:
            message = await websocket.receive_json()

            if not isinstance(message, dict):
                await websocket.send_json(
                    data = {
                        'type': 'error',
                        'detail': 'Ожидается JSON-объект'
                    }
                )
                continue

            if 'type' not in message or message.get('type') != 'chat':
                await websocket.send_json(
                    data = {
                        'type': 'error',
                        'detail': 'Неизвестный тип сообщения'
                    }
                )
                continue

            if 'text' not in message or not isinstance(message.get('text'), str) or message.get('text').strip() == '':
                await websocket.send_json(
                    data = {
                        'type': 'error',
                        'detail': 'Некорретная структура сообщения'
                    }
                )
                continue

            broadcast_message = {
                'type': 'chat',
                'text': message.get('text').strip()
            }

            await connection_manager.broadcast(broadcast_message)

    except WebSocketDisconnect as e:
        print(f'Клиент отключился. Код: {e.code}')

    finally:
        connection_manager.disconnect(user_id, websocket)
        
        if connected:
            await connection_manager.broadcast(
                {
                    'type': 'system',
                    'text': 'Клиент отключился'
                }
            )
