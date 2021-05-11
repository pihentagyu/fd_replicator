from actions.fd_devices import Devices, FdDevice

class ReplicatorMain:
    '''Replicator Main class'''
    def __init__(self):
        pass

    def new_device(self, **kwargs):
        '''create and return a new device'''
        return FdDevice(**kwargs)
