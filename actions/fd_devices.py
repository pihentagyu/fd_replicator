import hashlib
import logging
import os
import parted
import shlex
import shutil
import socket
import subprocess
import tempfile
import time

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
            usb_ids = {os.path.realpath(os.path.join(self.usbdir, usb)): usb.split(':')[1].split('.') for usb in os.listdir(self.usbdir) if 'usb' in usb and 'part' not in usb}
        except FileNotFoundError:
            return {}
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
                logging.info(f'Hub {hub} is not in usb port list. Something went wrong')
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
            direct_dev = self.get_direct_dev()
            for key, val in direct_dev.items():
                if val == self.port:
                    self.device = key

    def mount_device(self, **kwargs):
        '''Mount device on a tempdir, and return the directory name '''
        device = kwargs.get('device')
        if not device:
            device = self.device
        temp_dir = tempfile.mkdtemp()
        cmd = shlex.split(f'mount {device} {temp_dir}')
        #print(cmd)
        status = self.check_call(cmd, timeout=30)
        if status != 0:
            logging.info(f'Unable to mount device {device}.')
            return None, 1
        return temp_dir, 0

    def get_file_list(self):
        '''mount and list files from (source) device, then unmount'''
        try:
            directory, status = self.mount_device()
            if status == 0:
                files =  os.listdir(directory)    
                mount_status = self.check_mountpoint(mount_dir=directory)
                #TO DO: check status
                return files
            else:
                return None
        except OSError:
            return 1

    def create_dir(self, directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            logging.info(f'Error Creating {directory}. {e}')
            return 1
        return 0

    def create_checksums_files(self, **kwargs):
        '''Creates checksums from files in source_dir, or, if none given, to the current device'''
        source_dir = kwargs.get('source_dir')
        if not source_dir:
            source_dir = self.device_dir
            pc = 100
            adj = 0
        else:
            pc = 50
            adj = 50
        start = time.time()
        logging.info(f'Creating checksums on {source_dir}')
        mdsums = []
        self.num_files = self.count_files(source_dir)
        if self.num_files > 100:
            chunks = self.num_files // 100
        elif self.num_files > 2:
            chunks = self.num_files // 2
        else:
            chunks = 1
        num_copied = 0
        try:
            for dname in os.walk(source_dir):
                for fname in dname[2]:
                    mdsums.append(fname + ' ' + hashlib.md5(open(os.path.join(dname[0], fname), 'rb').read()).hexdigest())
                    num_copied += 1
                    if num_copied % chunks == 0:
                        self.calculate_and_emit(num_copied, self.num_files, pc=pc, adj=adj)

        except Exception as e:
            logging.error(f'Error creating checksums: {e}')
            return 1

        logging.info(f'Time creating checksums: {time.time()-start} seconds')
        return mdsums

    def compare_checksums_files(self, dest_dir):
        '''Compare checksums for newly copied fielse with those stored in the checksums file'''
    
        mdsums_dest = self.create_checksums_files(source_dir=dest_dir)
        if mdsums_dest == 1:
            return 1

        logging.info('Comparing checksums...')
        # Create sets from the two list, and compare
        diff = set(self.source_mdsums) ^ set(mdsums_dest)
        if diff:
            diffs = "\n".join(diff)
            logging.info(f'These files differ:\n {diffs}')
            return 1
        logging.info('Totals: {len()self.source_mdsums)}, {len(mdsums_dest)}')
        return  0
        
    def delete_all(self, **kwargs):
        directory = kwargs.get('directory')
        if not directory:
            directory = self.device_dir
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError as e:
                    return 1
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError as e:
                    print('rmdir error', e)
                    return 1
        return 0
    
    
    def delete_ignored(self, **kwargs):
        directory = kwargs.get('directory', None)
        if directory == None:
            directory = self.device_dir
        logging.info('removing unwanted files')
        to_delete = [os.path.join(directory, f) for f in os.listdir(directory) if f in self.ignore_files]
        logging.info(to_delete)
        for the_file in to_delete:
            if os.path.isfile(the_file):
                logging.info('removing file {the_file}')
                try:
                    os.remove(the_file)
                except OSError as e:
                    return 1

            elif os.path.isdir(the_file):
                logging.info(f'removing dir {the_file}')
                for root, dirs, files in os.walk(the_file, topdown=False):
                    for name in files:
                        logging.info(f'removing file {name}')
                        try:
                            os.remove(os.path.join(root, name))
                        except OSError as e:
                            logging.error(e)
                            return 1
                    for name in dirs:
                        logging.info(f'removing file {name}')
                        try:
                            os.rmdir(os.path.join(root, name))
                        except OSError as e:
                            logging.error(e)
                            return 1
                try:
                    os.rmdir(the_file)
                except OSError as e:
                    logging.error(e)
                    return 1
        return 0
   
    def count_files(self, directory):
        files = []
        if os.path.isdir(directory):
            for path, dirs, filenames in os.walk(directory):
                files.extend(filenames)
        return len(files)

    def makedirs(self, dest):
        if not os.path.exists(dest):
            try:
                r =os.makedirs(dest)
            except OSError as oe:
                logging.info(f'On creation of {dest}: {oe}')

    def calculate_and_emit(self, done, total, **kwargs):
        pc = kwargs.get('pc', 100)
        adj = kwargs.get('adj', 0)
        progress = int(round( (done / float(total)) * pc)) + adj
        self.emit(progress)


    def copy_files(self, **kwargs):
        source_dir = kwargs.get('source_dir', None)
        if source_dir == None:
            source_dir = self.source_dir
        dest_dir = kwargs.get('dest_dir', None)
        if dest_dir == None:
            dest_dir = self.device_dir

        self.num_files = self.count_files(source_dir)
        chunks = self.num_files // 100
        chunks = 1 if chunks == 0 else chunks

 
        if self.num_files > 0:
            self.makedirs(dest_dir)
 
            num_copied = 0
 
            for path, dirs, filenames in os.walk(source_dir):
                for directory in dirs:
                    _dest_dir = path.replace(source_dir,dest_dir)
                    self.makedirs(os.path.join(_dest_dir, directory))
                
                for sfile in filenames:
                    src_file = os.path.join(path, sfile)
                    dest_file = os.path.join(path.replace(source_dir, dest_dir), sfile)
                    try:
                        shutil.copy(src_file, dest_file)
                    except OSError as oe:
                        logging.info(f'On copy {source_dir} to {dest_dir}: {oe}')
                        return 1
                    num_copied += 1
                    if num_copied % chunks == 0:
                        if self.checksums:
                            pc = 50
                        else:
                            pc = 100
                        self.calculate_and_emit(num_copied, self.num_files, pc=pc)
        return 0

    def check_call(self, cmd, **kwargs): 
        timeout = kwargs.get('timeout')
        shell = kwargs.get('shell', False)
        device = kwargs.get('device')
        if not device:
            device = self.device
        try:
            status = subprocess.check_call(cmd, timeout=timeout, shell=shell)
        except subprocess.CalledProcessError as cpe:
            logging.info(f'{device}: {cpe}')
            status = cpe.returncode
        except subprocess.TimeoutExpired as te:
            logging.info(f'{device}: {te}')
            status = 1
        except Exception as e:
            logging.info(f'{device}: {e}')
            status = 1
        return status


    def format_device(self, **kwargs):
        # Wipe  shred_blocks of data from the device. Shredding the whole drive would take too much time
        device = kwargs.get('device')
        if not device:
            device = self.device
        '''Make sure the device is unmounted before beginning'''
        self.check_mountpoint(device=device)
        logging.info(f'Formatting device {device}...')
        try:
            dev = parted.getDevice(device)
        except parted._ped.IOException as e:
            logging.error(e)
            return 1
        except Exception as e:
            logging.error(e)
            return 1
    
        # First clobber it, removing all partitions
        try:
            status = dev.clobber()
        except parted._ped.IOException as e:
            logging.error(e)
            return 1
        except Exception as e:
            logging.error(e)
            return 1
        if status == False:
            return 1
        # Create a fresh disk
        try:
            disk = parted.freshDisk(dev, 'msdos')
        except parted._ped.DiskException as e:
            logging.info(f'Error formatting disk {device} {e}')
            return 1
        except:
            logging.info(f'Error formatting disk {device}.')
            return 1
        try:
            disk.commit()
        except parted._ped.DiskException as e:
            logging.info(f'Error formatting disk {device}. {e}')
            return 1
        except:
            logging.info(f'Error formatting disk {device}.')
            return 1

        ## Here it is possible to create partitions with disk using parted, but we'll just format
        # Make a file system
        cmd = shlex.split(f'mkfs.vfat -I {device}')
        logging.info(cmd)
        status = self.check_call(cmd, timeout=30)
        if status != 0:
            return 1
        cmd = shlex.split(f'fatlabel {device} {self.label}')
        status = self.check_call(cmd, timeout=30)
        return status
    
    def check_mountpoint(self, **kwargs):
        mount_dir = kwargs.get('mount_dir', None)
        device = kwargs.get('device', None)
        if device == None:
            device = self.device
        if mount_dir == None:
            cmd = shlex.split(f'umount {device}')
            status = self.check_call(cmd, timeout=30)
        else:
            # Check to see if directory is mounted
            cmd = shlex.split(f'mountpoint -q {mount_dir}') 
            #logging.info(cmd)
            status = self.check_call(cmd, timeout=30) 
            if status == 0:
                logging.info(f'Unmounting {mount_dir}')
                cmd = shlex.split(f'umount {mount_dir}')
                status = self.check_call(cmd, timeout=30)
        if status == 32:
            logging.info(f'Device {self.device} not mounted?')
        return status

    def copy_files_to_device(self):
        # First mount the device, get the mount directory and status
        logging.info('Copying to device...')
        device = self.device
        logging.info(device)
        self.device_dir, status = self.mount_device()
        if status != 0:
            status = self.format_device()
            #if mounting was unsuccessful, format device and create file system
            status = self.format_device()
            if status != 0:
               logging.info(f'Unable to format device {device}')
               return status
            #Once formated, try again to mount. Return status 1 if unable to mount
            self.device_dir, status = self.mount_device()
            if status != 0:
                logging.info(f'Unable to mount device {device}')
                return status
        # Copy the files from the local file directory to the device
        status = self.delete_all()
        if status != 0:
            #if removing files was unsuccessful, format device and create file system
            status = self.format_device()
            if status != 0:
               logging.info(f'Unable to format device {device}')
               return status
            #Once formated, try again to mount. Return status 1 if unable to mount
            self.device_dir, status = self.mount_device()
            if status != 0:
                logging.info(f'Unable to mount device {device}')
                return status
            
        logging.info('...to {device}')
        status = self.copy_files()
        if status != 0:
            self.check_mountpoint()
            return status
        # Compare checksums of the newly copied files
        if self.checksums:
            status = self.compare_checksums_files(self.device_dir)
            if status != 0:
                logging.info(f'Checksums did not match on device {device}')
                return status
        # Unmount the device
        status = self.check_mountpoint()
        if status != 0:
            logging.info(f'Failed to unmount on device {device}')
        else:
            status = self.remove_temp_dir()
            if status != 0:
                print(f'Error removing temp directory: {e}')
        return 0
    
    def remove_temp_dir(self):
        try:
            os.rmdir(self.device_dir)
        except OSError as e:
            return e
        return 0

    def prepare_to_copy(self, **kwargs):
        self.checksums = kwargs.get('checksums')
        self.progress_callback = kwargs.get('progress_callback')

        #device_dir Mount source device
        self.device_dir, status = self.mount_device(device=self.device)
        if status != 0:
            print('Unable to mount source directory!')
            return 1
        # Create checksums before copying
        if self.checksums:
            self.source_mdsums = self.create_checksums_files()
            if self.source_mdsums == 1:
                return 1
            #self.save_checksums(self.mdsums)
        return 0

    def emit(self, t):
        '''Emit a signal for threading, where t is between 0 and 100'''
        if self.hub:
            signal = t, self.hub, self.hub_coordinates
        else:
            signal = t, None, None
        self.progress_callback.emit(signal)
    
    def copy(self, source_device, source_dir, **kwargs):

        self.source_device = source_device
        self.source_dir = source_dir
        self.checksums = kwargs.get('checksums')
        self.progress_callback = kwargs.get('progress_callback')

        logging.info(f'copy from device: {source_device}')
        # Removed source device from devices

        copy_start = time.time()
        
        # multithread running copy_files_to_dev with devices list as args
        results = self.copy_files_to_device()
        status = self.check_mountpoint()
        if status != 0:
            logging.info(f'Failed to unmount device {self.device}')
        # List the devices and status for each
        logging.info(f'results {results}')
    
        # print the summary and times
        end = time.time()
        logging.info(f'Total time elapsed: {end - copy_start} seconds')
        total_time = end - copy_start

        return results
    


