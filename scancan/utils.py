from pyvalve import PyvalveSocket

async def get_clamav_connection() -> PyvalveSocket:
    """ Get clamav connection """
    pvs = await PyvalveSocket()
    pvs.set_persistant_connection(True)
    return pvs