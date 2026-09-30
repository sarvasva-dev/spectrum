import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VisualizerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join visualizer group
        self.group_name = 'visualizer'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave visualizer group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from room group
    async def backend_event(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(payload))
