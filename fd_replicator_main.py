from actions.fd_devices import Devices, FdDevice

class ReplicatorMain:
    '''Replicator Main class'''
    def __init__(self):
        self.fd_devices = Devices()
        self.config_dir = os.path.expanduser('~/.config/gochip')
        ## Do this after ReplicationMain is called?
        #self.check_config_dir()
        self.thread_count_file = os.path.join(self.config_dir, 'last_thread_count')
        #self.email_settings_file = os.path.join(self.config_dir, 'email_config.yaml')
        self.email_settings_file = EMAIL_SETTINGS_FILE # Change to the above

    def new_device(self, **kwargs):
        '''create and return a new device'''
        return FdDevice(**kwargs)

    
