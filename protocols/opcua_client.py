from asyncua import Client

from core.settings import settings


class OpcUaReader:
    NODES = {
        "temperature": "ns=2;s=Temperature",
        "pressure": "ns=2;s=Pressure",
        "flow_rate": "ns=2;s=FlowRate",
    }

    def __init__(self):
        self._client = Client(url=settings.opcua.url)
        if settings.opcua.username:
            self._client.set_user(settings.opcua.username)
            self._client.set_password(settings.opcua.password)

    async def read_all(self) -> dict[str, float]:
        values = {}
        async with self._client:
            for name, node_id in self.NODES.items():
                node = self._client.get_node(node_id)
                values[name] = await node.read_value()
        return values
