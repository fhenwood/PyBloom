from xbloom.connection import XBloomConnection
from xbloom.protocol import XBloomCommand

class BaseComponent:
    """Base class for XBloom components"""
    def __init__(self, connection: XBloomConnection):
        self._connection = connection

    async def _send(self, command: int, data: list = None) -> bool:
        pass # Client handles sending?
        # Ideally Components should use Connection directly?
        # But Client has Protocol Builder logic?
        # Protocol Builder is now in `xbloom.protocol.builder`.
        # So Components can build packets and send via Connection.
        # But Client also tracks STATE via Notification.
        # The Original design had Controller take `client`.
        # I'll modify Controllers to take `connection` AND Update State?
        # Or keep Controllers lightweight helpers that convert methods to commands.
        pass
