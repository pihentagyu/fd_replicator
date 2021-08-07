import os
import yaml

from actions.fd_devices import Devices, FdDevice
from actions.mail import Mail
from config.config import *

class ReplicatorMain:
    '''Replicator Main class'''
    def __init__(self):
        self.fd_devices = Devices()
        self.config_dir = os.path.expanduser('~/.config/fd_replicator')
        ## Do this after ReplicationMain is called?
        #self.check_and_create_dir(self.config_dir)()
        self.thread_count_file = os.path.join(self.config_dir, 'last_thread_count')
        #self.email_settings_file = os.path.join(self.config_dir, 'email_config.yaml')
        self.email_settings_file = EMAIL_SETTINGS_FILE # Change to the above

    def new_device(self, **kwargs):
        '''create and return a new device'''
        return FdDevice(**kwargs)

    def check_and_create_dir(self, directory):
        '''Create directory if it doesn't exist'''
        if not os.path.isdir(os.path.expanduser(directory)):
            try:
                os.makedirs(os.path.expanduser(directory))
            except OSError as ose:
                return ose

    def get_prev_thread_count(self):
        '''Open thread count file to get previously saved thread count'''
        if os.path.isfile(self.thread_count_file):
            try:
                with open(self.thread_count_file, 'r') as f:
                    prev_thread_count = f.read()
            except OSError:
                prev_thread_count = DEFAULT_THREAD_NUM
            try:
                prev_thread_count = int(prev_thread_count)
            except ValueError:
                prev_thread_count = DEFAULT_THREAD_NUM
        else:
            prev_thread_count = DEFAULT_THREAD_NUM

        return prev_thread_count

    def save_prev_thread_num(self, thread_count):
        '''Save thread numbers for future retrieval (so the number doesn't fall back to default between runs)'''
        try:
            with open(self.thread_count_file, 'w') as f:
                prev_thread_count = f.write(str(thread_count))
        except OSError: 
            pass

    def get_text_from_file(self, file_name):
        '''Return text from file'''
        with open(file_name, 'r') as t:
            text = t.read()
        return text

    def get_devices(self):
        '''Returns a list of hubs [], and a dict with hub and connected ports'''
        devices = self.fd_devices.get_usb_ids()
        connected_ports = self.fd_devices.get_hubs_with_mappings(devices)
        hubs = sorted(list(connected_ports.keys()))
        return hubs, connected_ports

    def get_direct_dev(self):
        '''get devices connected directly to the box'''
        direct_devices = self.fd_devices.get_direct_dev()
        if direct_devices:
            return direct_devices
        else:
            return {}

    def get_email_settings(self):
        '''Load yaml file and return dictionary'''
        if os.path.isfile(self.email_settings_file):
            try:
                with open(self.email_settings_file, 'r') as f:
                    email_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(e)
                email_data = None
            return email_data
        else:
            return None

    def save_email_settings(self, **kwargs):
        '''Save dictionary to yaml file'''
        with open(self.email_settings_file, 'w') as f:
            try:
                yaml.dump(kwargs, f, default_flow_style=False)
            except yaml.YAMLError as e:
                print(e)

    def send_notification(self, devices, failed, total_time, file_list):
        '''Send email notification after finished copying to all devices.'''
        contents = ', '.join(file_list) if file_list else 'None'
        replicator = self.fd_devices.replicator
        email_data = self.get_email_settings()
        self.mail = Mail()
        self.mail.connect()
        message_text = f'Finished copying on {replicator}.\n Contents: {contents}.\n\n {devices} devices. Failed: {failed}. Time elapsed (hh:mm:ss): {self.humanize_time(total_time)}'
        self.mail.compose_mail(message_text, email_data['from_addr'], email_data['to_addr'], subject=f'Finished Copying Devices on {replicator}')
        self.mail.send_mail(email_data['from_addr'], email_data['to_addr'])

    def humanize_time(self, secs, **kwargs):
        '''Given the number of seconds, return in (+) hours:minutes:seconds format'''
        add_plus_sign = kwargs.get('add_plus_sign', False)
        if secs == abs(secs):
            sign = '+'
        else:
            sign = None
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        if sign and add_plus_sign:
            return '%s %02d:%02d:%02d' % (sign, hours, mins, secs)
        else:
            return '%02d:%02d:%02d' % (hours, mins, secs)

