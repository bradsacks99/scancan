"""Clamav Connector"""
from pyvalve import PyvalveSocket, PyvalveConnectionError


class ClamAv:
    """
    ClamAv
    Provides an abstraction between Pyvalve and the application
    """
    def __init__(self) -> None:
        """
        ClamAv constructor

            Returns:
                None
        """
        self.pvs = None
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    async def ping(self):
        self.logger.info("Running ping command")
        await self.check_connect()
        return await self.pvs.ping();

    async def stats(self):
        self.logger.info("Running stats command")
        await self.check_connect()
        return await self.pvs.stats();

    async def scan(self, path):
        self.logger.info("Running scan command")
        await self.check_connect()
        return await self.pvs.scan(path);

    async def contscan(self, path):
        self.logger.info("Running contscan command")
        await self.check_connect()
        return await self.pvs.contscan(path);

    async def instream(self, file):
        self.logger.info("Running instream command")
        await self.check_connect()
        return await self.pvs.instream(file);

    async def connecting(self):
        self.logger.info("Connecting...")
        self.pvs = await PyvalveSocket()
        self.pvs.set_persistant_connection(True)

    async def check_connect(self):
        try:
            await self.pvs.ping()
        except PyvalveConnectionError:
            self.logger.info("PyvalveConnectionError, connecting...")
            await self.connecting()
        except AttributeError:
            self.logger.info("AttributeError, connecting...")
            await self.connecting()
