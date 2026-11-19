from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self._active_clients: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket) -> bool:
        try:
            await ws.accept()

            if user_id not in self._active_clients:
                self._active_clients[user_id] = set()

            self._active_clients[user_id].add(ws)
            return True
        
        except Exception as e:
            print(e)
            return False

    async def broadcast(self, client_message: dict) -> None:
        active_clients = [
            (user_id, client_ws)
            for user_id, connection in self._active_clients.items()
            for client_ws in connection
        ]

        for user_id, client_ws in active_clients:
            try:
                await client_ws.send_json(client_message)

            except Exception as e:
                self.disconnect(user_id, client_ws)
                print(e)

    async def send_personal(self, user_id: int, message: dict) -> None:
        if not self.is_online(user_id):
            return
        
        personal_connections = [
            client_ws for client_ws in self._active_clients[user_id]
        ]

        for client_ws in personal_connections:
            try:
                await client_ws.send_json(message)

            except Exception as e:
                self.disconnect(user_id, client_ws)
                print(e)

    def disconnect(self, user_id: int, client_ws: WebSocket) -> None:
        if user_id not in self._active_clients:
            return
        
        self._active_clients[user_id].discard(client_ws)

        # если pool клиентских соединений пуст, то в таком случае удалям клиентский id
        if not self._active_clients[user_id]:
            del self._active_clients[user_id]

    def is_online(self, user_id: int) -> bool:
        return user_id in self._active_clients

connection_manager = ConnectionManager()
