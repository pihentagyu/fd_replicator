import logging
import os
import shlex
import socket
import subprocess

from config.config import *

class Devices:
    def __init__(self):
        self.mapping_file = MAPPING_FILE 
        self.usb_ports = USB_PORTS 
        self.usbdir = USBDIR 
        self.hub_rows = HUB_ROWS 
        self.mappings = self.get_mappings()
        self.replicator = socket.gethostname() 

    def get_mappings(self):
        '''Opens mapping file, and returns a list with the port numbers in order'''
        with open(self.mapping_file) as f:
            mappings = f.readlines()
        mappings = list(filter(None, [m.rstrip('\n') for m in mappings]))
        return mappings

    def get_usb_ids(self):
        '''Returns a dictionary of the disk-path: usb ids from /dev/disk/by-path. Removes the partition listings'''
        try:
            print(self.usbdir)
            print(os.listdir(self.usbdir))
            usb_ids = {os.path.realpath(os.path.join(self.usbdir, usb)): usb.split(':')[1].split('.') for usb in os.listdir(self.usbdir) if 'usb' in usb and 'part' not in usb}
        except FileNotFoundError:
            return ['']
        return usb_ids
    
    def get_direct_dev(self):
        dir_dev =  {key: '.'.join(val) for key, val in self.get_usb_ids().items() if '.'.join(val) in self.usb_ports}
        return dir_dev
    
    def get_dev_loc_from_mapping(self, dev_addr):
        if dev_addr in self.mappings:
            return self.mappings.index(dev_addr)
        else:
            return 

    def get_dev_map_location(self, dev_addr):
        dev_loc = self.get_dev_loc_from_mapping(dev_addr)
        if dev_loc == None:
            return None
        if dev_loc > self.hub_rows - 1:
            return (dev_loc - self.hub_rows, 1)
        else:
            return(dev_loc, 0)

    def get_hubs_with_mappings(self, usb_ids):
        '''Returns dict of hubs eg: {'1': [('1.2.3', '/dev/sdb', (0.0)), ('1.3.5', '/dev/sdc', (0.1))]}'''
        hubs = {}
        for key, val in usb_ids.items():
            dev_name = key
            hub = val[0]
            if hub in self.usb_ports:
                dev_addr = '.'.join(val[1:])
                dev_map_location =  self.get_dev_map_location(dev_addr)
            else:
                logging.info('Hub {} is not in usb port list. Something went wrong'.format(hub))
                dev_addr = None
                dev_map_location = None
            if dev_map_location != None:
                if hub not in hubs.keys():
                    hubs[hub] = [(dev_addr, dev_name, dev_map_location)]
                else:
                    hubs[hub].append((dev_addr, dev_name, dev_map_location))
        return hubs

class FdDevice:
    '''Actions pertaining to particular devices'''
    def __init__(self, **kwargs):
        self.port = kwargs.get('port', None)
        self.hub = kwargs.get('hub', None)
        self.hub_coordinates = kwargs.get('hub_coordinates', None)
        self.device = kwargs.get('device', None)
        self.device_dir = kwargs.get('device_dir', None)
        self.source_mdsums = kwargs.get('source_mdsums', None)
        self.devices = Devices()
        self.ignore_files = IGNORED_FILES
        self.label = DEVICE_LABEL

    def get_device_from_port(self):
        self.device = None
        if self.port:
            direct_dev = self.gd.get_direct_dev()
            for key, val in direct_dev.items():
                if val == self.port:
                    self.device = key

    def get_file_list(self):
        '''mount and list files from (source) device, then unmount'''
        try:
            directory, status = self.mount_device()
            if status == 0:
                files =  os.listdir(directory)    
                mount_status = self.check_mountpoint(mount_dir=directory)
                return files
                '''to do: return mount status?'''
            else:
                return None
        except OSError:
            return 1
