"""Clamav Connector"""
from pyvalve import PyvalveSocket, PyvalveConnectionError, PyvalveNetwork


class ClamAv:
    """
    ClamAv
    Provides an abstraction between Pyvalve and the application
    """
    def __init__(self, conf) -> None:
        """
        ClamAv constructor

            Returns:
                None
        """
        self.pvs = None
        self.logger = None
        self.conf = conf

    def set_logger(self, logger):
        """ Set Logger """
        self.logger = logger

    async def ping(self):
        """ Ping """
        self.logger.info("Running ping command")
        await self.check_connect()
        return await self.pvs.ping()

    async def stats(self):
        """ Stats """
        self.logger.info("Running stats command")
        await self.check_connect()
        return await self.pvs.stats()

    async def scan(self, path):
        """ Scan """
        self.logger.info("Running scan command")
        await self.check_connect()
        return await self.pvs.scan(path)

    async def contscan(self, path):
        """ Cont Scan """
        self.logger.info("Running contscan command")
        await self.check_connect()
        return await self.pvs.contscan(path)

    async def instream(self, file):
        """ Instream """
        self.logger.info("Running instream command")
        await self.check_connect()
        return await self.pvs.instream(file)

    async def connecting(self):
        """ Connecting """
        self.logger.info("Connecting...")
        if self.conf.clamd_conn == 'net':
            self.pvs = await PyvalveNetwork(
                self.conf.clamd_host,
                self.conf.clamd_port
            )
        else:
            self.pvs = await PyvalveSocket(self.conf.clamd_socket)
        self.pvs.set_persistant_connection(True)

    async def check_connect(self):
        """ Check Connect """
        try:
            await self.pvs.ping()
        except PyvalveConnectionError:
            self.logger.info("PyvalveConnectionError, connecting...")
            await self.connecting()
        except AttributeError:
            self.logger.info("AttributeError, connecting...")
            await self.connecting()
