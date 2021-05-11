#!/usr/bin/python

import unittest
from unittest.mock import MagicMock

from fd_replicator_main import *
import actions.fd_devices as fd_devices
from actions.fd_devices import Devices, FdDevice


class ReplicatorMainTests(unittest.TestCase):
    def setUp(self):
        pass

class DevicesTests(unittest.TestCase):
    def setUp(self):
        fd_devices.MAPPING_FILE = 'dev_port_mapping_test'
        self.devices_dict = {'/dev/sdh': ['1', '2', '6'], '/dev/sdn': ['1', '6', '4', '4'], '/dev/sdv': ['1', '1', '5'], 
                '/dev/sdr': ['1', '1', '4'], '/dev/sds': ['1', '3', '4'], '/dev/sdj': ['1', '3', '2'], 
                '/dev/sdc': ['1', '2', '4'], '/dev/sdk': ['1', '4', '2'], '/dev/sdad': ['1', '4', '7'], 
                '/dev/sdw': ['1', '3', '5'], '/dev/sdg': ['1', '4', '1'], '/dev/sdx': ['1', '1', '6'], 
                '/dev/sdq': ['1', '4', '3'], '/dev/sdab': ['1', '3', '7'], '/dev/sdac': ['1', '4', '6'],
                '/dev/sdy': ['1', '3', '6'], '/dev/sdf': ['1', '3', '1'], '/dev/sdm': ['1', '1', '3'], 
                '/dev/sdl': ['1', '2', '7'], '/dev/sdo': ['1', '3', '3'], '/dev/sdaa': ['1', '4', '5'], 
                '/dev/sdi': ['1', '1', '2'], '/dev/sdz': ['1', '1', '7'], '/dev/sdu': ['1', '2', '2'], 
                '/dev/sdt': ['1', '4', '4'], '/dev/sde': ['1', '1', '1'], '/dev/sdp': ['2', '2', '1'], 
                '/dev/sdd': ['2', '2', '5'], '/dev/sdb': ['2', '2', '3']} 
        self.devices = Devices()

    def test_get_mappings(self):
        mappings = self.devices.get_mappings()
        self.assertEqual(mappings[0], '3.6')
        self.assertEqual(mappings[27], '2.4')
        self.assertEqual(mappings[-1], '6.3.7')

    #def test_get_replicator(self):
    #    fd_devices.subprocess = MagicMock()
    #    fd_devices.subprocess.check_output = MagicMock(return_value=b'raspberry ')
    #    replicator = self.devices.get_replicator()
    #    fd_devices.subprocess.check_output.assert_called_with(['hostname'], shell=True)
    #    self.assertEqual(replicator, 'raspberry')

    def test_get_usb_ids(self):
        fd_devices.os.listdir = MagicMock(return_value=['pci-0000:00:14.0-usb-0:4:1.0-scsi-0:0:0:0-part1', 
            'pci-0000:00:14.0-usb-0:4:1.0-scsi-0:0:0:0'])
        fd_devices.os.path.realpath = MagicMock(return_value='/dev/sda')
        usb_ids = self.devices.get_usb_ids()
        fd_devices.os.listdir.assert_called_with(self.devices.usbdir)
        self.assertEqual(usb_ids,{'/dev/sda': ['00']}) 

    def test_get_direct_dev(self):
        self.devices.get_usb_ids = MagicMock(return_value={'/dev/sda': ['00']})
        self.devices.usb_ports = ['00']
        direct_dev = self.devices.get_direct_dev()
        self.devices.get_usb_ids.assert_called()
        print(direct_dev)
        self.assertEqual(direct_dev, {'/dev/sda': '00'})
        
    def test_get_dev_loc_from_mapping(self):
        self.devices.mappings = ['3.6', '3.7', '3.8', 1.7]
        dev_add = '3.7'
        dev_loc = self.devices.get_dev_loc_from_mapping(dev_add)
        self.assertEqual(dev_loc, 1)

        dev_add = '4.7'
        dev_loc = self.devices.get_dev_loc_from_mapping(dev_add)
        self.assertEqual(dev_loc, None)

    def test_get_dev_map_location(self):
        self.devices.get_dev_loc_from_mapping = MagicMock(return_value=3)
        self.devices.hub_rows = 27
        dev_addr = '3.7'
        dev_map_location = self.devices.get_dev_map_location(dev_addr)
        self.assertEqual(dev_map_location, (3, 0))

        self.devices.get_dev_loc_from_mapping = MagicMock(return_value=26)
        self.devices.hub_rows = 27
        dev_addr = '1.7'
        dev_map_location = self.devices.get_dev_map_location(dev_addr)
        self.assertEqual(dev_map_location, (26, 0))

        self.devices.get_dev_loc_from_mapping = MagicMock(return_value=27)
        self.devices.hub_rows = 27
        dev_addr = '1.7'
        dev_map_location = self.devices.get_dev_map_location(dev_addr)
        self.assertEqual(dev_map_location, (0, 1))

        self.devices.get_dev_loc_from_mapping = MagicMock(return_value=54)
        self.devices.hub_rows = 27
        dev_addr = '1.7'
        dev_map_location = self.devices.get_dev_map_location(dev_addr)
        self.assertEqual(dev_map_location, (27, 1))

    def test_get_hubs_with_mappings(self):
        self.devices.usb_ports = {'1', '2'}
        hubs = self.devices.get_hubs_with_mappings(self.devices_dict)
        self.assertIsInstance(hubs, dict)
        self.assertEqual(len(hubs['1']), 26)
        self.assertEqual(len(hubs['2']), 3)
        self.assertIsInstance(hubs['1'][0], tuple)
        self.assertEqual(hubs['1'][0][0], '2.6')
        #self.assertEqual(hubs['1'][0], '/dev/')
        print('get hubs with mappings: returned results: {}'.format(hubs))
        for dev in hubs['1']:
            if dev[0] == '2.6':
                self.assertEqual(dev[1], '/dev/sdh')
                self.assertEqual(dev[2], (5,1))
            if dev[1] == '/dev/sdab':
                self.assertEqual(dev[0], '3.7')
                self.assertEqual(dev[2], (1,0))

class FdDeviceTests(unittest.TestCase):
    def setUp(self):
        self.devices = Devices()
        self.fd_device = FdDevice()
        self.replicator_main = ReplicatorMain()
        self.fd_device.source_object = self.replicator_main.new_device()    
        self.fd_device.source_object.device = '/dev/sda'
        self.fd_device.source_object.device_dir = '/tmp/sda'
        self.dest_object = self.replicator_main.new_device()    
        self.dest_object.device = '/dev/sdb'

    def test_get_device_from_port(self):
        self.fd_device.source_object.port = '1.2.6'
        self.fd_device.get_direct_dev = MagicMock(return_value={'/dev/sda': '1.2.6'})
        self.fd_device.get_device_from_port() 
        self.assertEqual(self.fd_device.source_object.device, '/dev/sda')

    def test_get_file_list(self):
        pass


#    def test_check_call(self):
#        timeout = 10
#        #test without timeout
#        cmd = shlex.split('ls -l')
#        status = self.fd_device.check_call(cmd)
#        self.assertEqual(status, 0)
#
#        #test timeout error
#        cmd = shlex.split('sleep 10')
#        status = self.fd_device.check_call(cmd, timeout=timeout)
#        self.assertEqual(status, 1)
#
#        #test CalledProcesserError
#        status = self.fd_device.check_call(['exit 1'], shell=True)
#        self.assertEqual(status, 1)
#        
#    
#    def test_prepare_to_copy(self):
#        self.source_object.mount_device = MagicMock(return_value=('/tmp/tmpdir', 0))
#        self.source_object.delete_ignored = MagicMock(return_value=0)
#        self.source_object.create_checksums_files = MagicMock(return_value=0)
#        status = self.source_object.prepare_to_copy(checksums=True)
#        self.assertEqual(status, 0)
#
#    def test_copy(self):
#        self.dest_object.copy_files_to_device = MagicMock(return_value='These are the results')
#        self.dest_object.check_mountpoint = MagicMock(return_value=0)
#        results = self.dest_object.copy(self.source_object.device, self.source_object.device_dir, checksums=True)
#        self.assertEqual(results, 'These are the results')
#
#    def test_copy_files_to_device(self):
#        self.dest_object.source_device = '/dev/sda'
#        self.dest_object.source_dir = '/tmp/sda'
#        self.dest_object.mount_device = MagicMock(return_value=('/tmp/tmpdir', 0))
#        self.dest_object.format_device = MagicMock(return_value=0)
#        self.dest_object.delete_all = MagicMock(return_value=0)
#        self.dest_object.copy_files = MagicMock(return_value=0)
#        self.dest_object.check_mountpoint = MagicMock(return_value=0)
#        self.dest_object.checksums = True
#        self.dest_object.compare_checksums_files = MagicMock(return_value=0)
#        self.dest_object.remove_temp_dir = MagicMock(return_value=0)
#        status = self.dest_object.copy_files_to_device()
#        self.assertEqual(status, 0)
#
#        self.dest_object.check_mountpoint = MagicMock(return_value=32)
#        status = self.dest_object.copy_files_to_device()
#        self.assertEqual(status, 0)
#
#        self.dest_object.mount_device = MagicMock(return_value=('/tmp/tmpdir', 1))
#        self.dest_object.format_device = MagicMock(return_value=1)
#        status = self.dest_object.copy_files_to_device()
#        self.assertEqual(status, 1)
#
#    def test_check_mountpoint(self):
#        pass
#
#    def test_copy_files(self):
#        self.dest_object.source_dir = '/tmp/sda'
#        self.dest_object.dest_dir = '/tmp/sdb'
#
#    def test_create_checksums_files(self):
#        self.fd_device.checksums = True
#        signals = WorkerSignals()
#        progress = signals.progress
#        self.fd_device.progress_callback = progress
#        self.fd_device.device_dir = tempfile.mkdtemp()
#        for dir in ('test1', 'test2'):
#            try:
#                os.mkdir(os.path.join(self.fd_device.device_dir, dir))
#            except:
#                print('error creating dir {}'.format(dir))
#                return
#
#            for f in ('test1.txt', 'test2.txt'):
#                with open(os.path.join(self.fd_device.device_dir, dir, f), 'w') as stream:
#                        stream.write('hello, this is a test. {}, {}'.format(dir, f))
#
#
#        checksums = self.fd_device.create_checksums_files()
#        self.assertIsInstance(checksums, list)
#        #self.assertEqual(checksums[0].split(' ')[0], 'test1.txt')
#        print(checksums)
#        #self.assertEqual(status, 0)
#
#        shutil.rmtree(self.fd_device.device_dir)
#
#
#    def test_calculate_and_emit(self):
#        def get_emit(x):
#            self.x = x
#        self.fd_device.emit = lambda x: get_emit(x)
#        self.fd_device.calculate_and_emit(10, 100)
#        self.assertEqual(self.x, 10)
#        self.fd_device.calculate_and_emit(10, 100, adj=50, pc=50)
#        self.assertEqual(self.x, 55)
#
#
#
#
#    def test_create_dir(self):
#        pass
#
#    def test_create_checksums(self):
#        pass
#
#
#    def test_compare_checksums_files(self):
#        device = self.fd_main.new_device()    
#        checksums = ['seg-221.m4s c59b6068f8e29144a8843dae91417a46', 'seg-222.m4s d303ee4ea9b83b23bd8ef575ba91e0c9', 'seg-224.m4s fd938e0661353df437cf71297f614e79', 'seg-223.m4s 19fcaa424456d3daf69e9e63d7c8cae4', 'seg-225.m4s f35f8f20db85b49abbd4204ba767d710', 'seg-226.m4s 10061ed9b33de483c5757d075e8c4eba', 'seg-227.m4s d58560ecc2d37039ab190c3f1be4aed7', 'seg-228.m4s ba4 2fb9edf72c11f92395b646baa74d', 'seg-229.m4s ee2dd1ee204d471bac4764a1f611c973', 'seg-230.m4s 9af2ec530ddf9feeea9241dd7da9ce21', 'seg-233.m4s fc5d352bbedd7327b00e034a5f33f79c', 'seg-231.m4s 4990ffd97e014b5e315671c26195744d', 'seg-232.m4s 4a2e62338083729cd114ddcf4685e00b']
#        bad_checksums = ['seg-221.m4s c59b6068f8e29144a8843dae91417a46', 'seg-222.m4s d303ee4ea9b83b23bd8ef575ba91e0c9', 'seg-224.m4s fd938e0661353df437cf71297f614e79', 'seg-223.m4s 41caab57470a3696c106f7edd0e79ad5', 'seg-225.m4s f35f8f20db85b49abbd4204ba767d710', 'seg-226.m4s 10061ed9b33de483c5757d075e8c4eba', 'seg-227.m4s d58560ecc2d37039ab190c3f1be4aed7', 'seg-228.m4s ba4 2fb9edf72c11f92395b646baa74d', 'seg-229.m4s ee2dd1ee204d471bac4764a1f611c973', 'seg-230.m4s 9af2ec530ddf9feeea9241dd7da9ce21', 'seg-233.m4s fc5d352bbedd7327b00e034a5f33f79c', 'seg-231.m4s 4990ffd97e014b5e315671c26195744d', 'seg-232.m4s 4a2e62338083729cd114ddcf4685e00b']
#        device.source_mdsums = checksums
#        device.create_checksums_files = MagicMock(return_value=checksums)
#        status = device.compare_checksums_files('/tmp/tmpb8y1qgwb')
#        self.assertEqual(status, 0)
#        device.create_checksums_files = MagicMock(return_value=bad_checksums)
#        status = device.compare_checksums_files('/tmp/tmpb8y1qgwb')
#        self.assertEqual(status, 1)
#
#    def test_compare_checksums(self):
#        pass
#
#    def test_delete_all(self):
#        pass
#
#    def test_delete_ignored(self):
#        pass
#
#    def test_copy_files(self):
#        pass
#
#    def test_mount_device(self):
#        self.fd_device.check_call = MagicMock(return_value=0)
#        results = self.fd_device.mount_device()
#        self.assertIsInstance(results, tuple)
#        self.assertEqual(results[1], 0)
#
#    def test_format_device(self):
#        pass
#
if __name__ == '__main__':
    unittest.main()
