#!/usr/bin/python

from email.mime.multipart import MIMEMultipart
import hashlib
import shlex
import string
import subprocess
import unittest
from unittest.mock import MagicMock, patch, mock_open, call, DEFAULT

import fd_replicator_main
from fd_replicator_main import *
import actions.fd_devices as fd_devices
from actions.fd_devices import Devices, FdDevice
from actions.mail import Mail


class ReplicatorMainTests(unittest.TestCase):
    def setUp(self):
        self.replicator_main = ReplicatorMain()
        self.replicator_main.fd_devices = MagicMock()

    @patch('actions.fd_devices.FdDevice')
    def test_new_device(self, mock_FdDevice):
        device = self.replicator_main.new_device()
        self.assertIsInstance(device, FdDevice)

    @patch('fd_replicator_main.os.path.isdir', side_effect=(False, True, False))
    @patch('fd_replicator_main.os.makedirs', side_effect=(None, OSError('os error')))
    def test_check_and_create_dir(self, mock_makedirs, mock_isdir):
       resp = self.replicator_main.check_and_create_dir('/foo/bar')
       self.assertEqual(resp, None)
       mock_isdir.assert_called_with('/foo/bar')
       mock_makedirs.assert_called_with('/foo/bar')

       resp = self.replicator_main.check_and_create_dir('/foo/bar')
       self.assertEqual(resp, None)
       mock_isdir.assert_called_with('/foo/bar')

       resp = self.replicator_main.check_and_create_dir('/foo/bar')
       mock_isdir.assert_called_with('/foo/bar')
       mock_makedirs.assert_called_with('/foo/bar')
       self.assertIsInstance(resp, OSError)

       self.assertEqual(mock_makedirs.call_count, 2)

    @patch('fd_replicator_main.os.path.isfile', side_effect=(True, True, True, False))#)#, 
    def test_get_prev_thread_count(self, mock_isfile):
        with patch('fd_replicator_main.open', mock_open(read_data='10')):#, side_effect=(None, OSError, ValueError))
            fd_replicator_main.DEFAULT_THREAD_NUM = 15
            self.replicator_main.thread_count_file = 'foo/bar.txt'
            thread_ct = self.replicator_main.get_prev_thread_count()
            self.assertEqual(thread_ct, 10)
            mock_isfile.assert_called_with('foo/bar.txt')

        fd_replicator_main.open = MagicMock(side_effect=OSError)
        thread_ct = self.replicator_main.get_prev_thread_count()
        self.assertEqual(thread_ct, 15)
        mock_isfile.assert_called_with('foo/bar.txt')

        with patch('fd_replicator_main.open', mock_open(read_data='not a number')):#, side_effect=(None, OSError, ValueError))
            thread_ct = self.replicator_main.get_prev_thread_count()
            self.assertEqual(thread_ct, 15)
            mock_isfile.assert_called_with('foo/bar.txt')

        thread_ct = self.replicator_main.get_prev_thread_count()
        self.assertEqual(thread_ct, 15)
        mock_isfile.assert_called_with('foo/bar.txt')

    def test_get_prev_thread_count(self):
        m = mock_open()
        self.replicator_main.thread_count_file = './foobar'
        with patch('fd_replicator_main.open', m):
            self.replicator_main.save_prev_thread_num(10)

        m.assert_called_once_with('./foobar', 'w')
        h = m()
        h.write.assert_called_with('10')

    def test_get_text_from_file(self):
        m = mock_open(read_data='This is the text')
        with patch('fd_replicator_main.open', m):
            text = self.replicator_main.get_text_from_file('./help')
        self.assertEqual(text, 'This is the text')
        m.assert_called_once_with('./help', 'r')

    def test_get_devices(self):
        self.replicator_main.fd_devices.get_usb_ids = MagicMock(return_value={'/dev/sda': ['00']})
        self.replicator_main.fd_devices.get_hubs_with_mappings = MagicMock(return_value={'1': [('2.6', '/dev/sdh', (5, 1)), 
            ('6.4.4', '/dev/sdn', (14, 1)), 
            ('1.5', '/dev/sdv', (7, 1)), 
            ('1.4', '/dev/sdr', (8, 1)), ('3.4', '/dev/sds', (5, 0)), ('3.2', '/dev/sdj', (3, 0)), ('2.4', '/dev/sdc', (0, 1)), 
            ('4.2', '/dev/sdk', (11, 0)), ('4.7', '/dev/sdad', (9, 0)), ('3.5', '/dev/sdw', (6, 0)), ('4.1', '/dev/sdg', (10, 0)), 
            ('1.6', '/dev/sdx', (13, 1)), ('4.3', '/dev/sdq', (12, 0)), ('3.7', '/dev/sdab', (1, 0)), ('4.6', '/dev/sdac', (8, 0)),
            ('3.6', '/dev/sdy', (0, 0)), ('3.1', '/dev/sdf', (2, 0)), ('1.3', '/dev/sdm', (9, 1)), ('2.7', '/dev/sdl', (4, 1)), 
            ('3.3', '/dev/sdo', (4, 0)), ('4.5', '/dev/sdaa', (7, 0)), ('1.2', '/dev/sdi', (10, 1)), ('1.7', '/dev/sdz', (12, 1)), 
            ('2.2', '/dev/sdu', (2, 1)), ('4.4', '/dev/sdt', (13, 0)), ('1.1', '/dev/sde', (11, 1))], '2': [('2.1', '/dev/sdp', (3, 1)), 
            ('2.5', '/dev/sdd', (6, 1)), ('2.3', '/dev/sdb', (1, 1))]})
        hubs, connected_ports = self.replicator_main.get_devices()
        print(hubs)
        print(connected_ports)

    def test_get_direct_dev(self):
        self.replicator_main.fd_devices.get_direct_dev = MagicMock(side_effect=[{'/dev/sda': '00'}, None])
        direct_devices = self.replicator_main.get_direct_dev()
        self.assertEqual(direct_devices, {'/dev/sda': '00'})
        direct_devices = self.replicator_main.get_direct_dev()
        self.assertEqual(direct_devices, {})

    @patch('fd_replicator_main.os.path.isfile', side_effect=(True, True, False))
    @patch('fd_replicator_main.yaml.safe_load', return_value={'from_addr': 'foo@bar.com', 'to_addr':['foobar@baz']})
    def test_get_mail_settings(self, mock_safe_load, mock_isfile):
        m = mock_open(read_data='from_addr\n foo@bar.com\n to_addr\n foobar@baz')
        with patch('fd_replicator_main.open', m):
            email_data = self.replicator_main.get_email_settings()
        self.assertEqual(email_data, {'from_addr': 'foo@bar.com', 'to_addr':['foobar@baz']})
        m.assert_called_once_with('./config/email_config.yaml', 'r')

    @patch('fd_replicator_main.yaml.dump')
    def test_save_email_settings(self, mock_dump):
        m = mock_open()
        with patch('fd_replicator_main.open', m):
            email_data = self.replicator_main.save_email_settings(a='b', b='c')
        mock_dump.assert_called_with({'a': 'b', 'b': 'c'}, m(), default_flow_style=False)

    @patch('fd_replicator_main.Mail')
    def test_send_notifications(self, mock_Mail):
        self.replicator_main.fd_devices.replicator = 'LinuxBox'
        self.replicator_main.get_email_settings = MagicMock(return_value={'from_addr': 'foobar@baz', 'to_addr': 'foobar2@baz'})
        self.replicator_main.humanize_time = MagicMock(return_value='2:22:22')
        devices = ['sdaa', 'sdab', 'sdac']
        failed = []
        total_time = 344332
        file_list = ['abc.txt', 'cde.txt']
        contents = ', '.join(file_list)
        message_text = f'Finished copying on LinuxBox.\n Contents: {contents}.\n\n {devices} devices. Failed: {failed}. Time elapsed (hh:mm:ss): 2:22:22'
        self.replicator_main.send_notification(devices, failed, total_time, file_list)
        subject = 'Finished Copying Devices on LinuxBox'

        self.replicator_main.get_email_settings.assert_called()
        mock_Mail.assert_called()
        self.replicator_main.mail.connect.assert_called()
        self.replicator_main.mail.compose_mail.assert_called_with(message_text, 'foobar@baz', 'foobar2@baz', subject=subject)
        self.replicator_main.mail.send_mail.assert_called_with('foobar@baz', 'foobar2@baz')

    def test_humanize_time(self):
        htime = self.replicator_main.humanize_time(60)
        self.assertEqual(htime, '00:01:00')

        htime = self.replicator_main.humanize_time(60, add_plus_sign=True)
        self.assertEqual(htime, '+ 00:01:00')

        htime = self.replicator_main.humanize_time(3600)
        self.assertEqual(htime, '01:00:00')

        htime = self.replicator_main.humanize_time(3661)
        self.assertEqual(htime, '01:01:01')

        htime = self.replicator_main.humanize_time(360000)
        self.assertEqual(htime, '100:00:00')

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

    @patch('actions.fd_devices.os.listdir', return_value=['pci-0000:00:14.0-usb-0:4:1.0-scsi-0:0:0:0-part1', 
            'pci-0000:00:14.0-usb-0:4:1.0-scsi-0:0:0:0'])
    def test_get_usb_ids(self, mock_listdir):
        fd_devices.os.path.realpath = MagicMock(return_value='/dev/sda')
        usb_ids = self.devices.get_usb_ids()
        mock_listdir.assert_called_with(self.devices.usbdir)
        self.assertEqual(usb_ids,{'/dev/sda': ['00']}) 

        fd_devices.os.path.realpath = MagicMock(side_effect=FileNotFoundError())
        usb_ids = self.devices.get_usb_ids()
        mock_listdir.assert_called_with(self.devices.usbdir)
        self.assertEqual(usb_ids,{}) 

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
        self.fd_device = FdDevice(port='1.2.3', device_dir='/foo/bar/')

    def test_get_device_from_port(self):
        self.fd_device.port = '1.2.6'
        self.fd_device.get_direct_dev = MagicMock(return_value={'/dev/sda': '1.2.6'})
        self.fd_device.get_device_from_port() 
        self.assertEqual(self.fd_device.device, '/dev/sda')

    @patch('actions.fd_devices.tempfile.mkdtemp', return_value='foo/bar')
    def test_mount_device(self, mock_tempfile):
        self.fd_device.check_call = MagicMock(return_value=0)
        results = self.fd_device.mount_device(device='/dev/sdb')
        self.assertIsInstance(results, tuple)
        self.assertEqual(results[0], 'foo/bar')
        self.assertEqual(results[1], 0)

        self.fd_device.device = '/dev/sdc'
        self.fd_device.check_call = MagicMock(return_value=0)
        results = self.fd_device.mount_device()
        self.assertIsInstance(results, tuple)
        self.assertEqual(results[0], 'foo/bar')
        self.assertEqual(results[1], 0)

        self.fd_device.check_call = MagicMock(return_value=1)
        results = self.fd_device.mount_device(device='/dev/sdb')
        self.assertIsInstance(results, tuple)
        self.assertEqual(results[0], None)
        self.assertEqual(results[1], 1)

    @patch('actions.fd_devices.os.makedirs',side_effect=OSError('OS Error'))
    @patch('actions.fd_devices.logging.info')
    def test_create_dir(self, mock_info, mock_makedirs):
        status = self.fd_device.create_dir('/foo/bar')
        mock_info.assert_called_with('Error Creating /foo/bar. OS Error')
        self.assertEqual(status, 1)

    @patch('actions.fd_devices.os.listdir', return_value=['a.txt', 'b.txt'])
    def test_get_file_list(self, mock_list_dir):
        self.fd_device.mount_device = MagicMock(return_value=('/foo/bar', 0))
        self.fd_device.check_mountpoint = MagicMock(return_value=0)
        files = self.fd_device.get_file_list()
        self.assertIsInstance(files, list)
        self.assertEqual(files, ['a.txt', 'b.txt'])

        self.fd_device.mount_device = MagicMock(return_value=(None, 1))
        self.fd_device.check_mountpoint = MagicMock(return_value=0)
        files = self.fd_device.get_file_list()
        self.assertEqual(files, None)

    @patch('actions.fd_devices.time.time')
    @patch('actions.fd_devices.logging.info')
    @patch('actions.fd_devices.hashlib')
    @patch('actions.fd_devices.os.walk',return_value=[('.', ['a', 'b'], ['a.txt']), ('./a', [], ['1.txt', '2.txt', '3.txt']), ('./b', [], ['4.txt', '5.txt', '6.txt'])])     
    @patch('actions.fd_devices.os.path.join')
    @patch('actions.fd_devices.open')
    def test_create_checksums_files(self, mock_open, mock_join, mock_walk, mock_hashlib, mock_info, mock_time):
        self.fd_device.device_dir = '/foo/bar'
        md5_test = hashlib.md5(string.ascii_letters.encode())
        mock_hashlib.md5 = MagicMock(return_value=md5_test)
        self.fd_device.calculate_and_emit = MagicMock()
        self.fd_device.count_files = MagicMock(return_value=100)
        mdsums = self.fd_device.create_checksums_files(source_dir='/foo/bar')
        self.assertEqual(mdsums[0], 'a.txt ' + md5_test.hexdigest())

    def test_compare_checksums_files(self):
        checksums = ['seg-221.m4s c59b6068f8e29144a8843dae91417a46', 'seg-222.m4s d303ee4ea9b83b23bd8ef575ba91e0c9', 'seg-224.m4s fd938e0661353df437cf71297f614e79', 'seg-223.m4s 19fcaa424456d3daf69e9e63d7c8cae4', 'seg-225.m4s f35f8f20db85b49abbd4204ba767d710', 'seg-226.m4s 10061ed9b33de483c5757d075e8c4eba', 'seg-227.m4s d58560ecc2d37039ab190c3f1be4aed7', 'seg-228.m4s ba4 2fb9edf72c11f92395b646baa74d', 'seg-229.m4s ee2dd1ee204d471bac4764a1f611c973', 'seg-230.m4s 9af2ec530ddf9feeea9241dd7da9ce21', 'seg-233.m4s fc5d352bbedd7327b00e034a5f33f79c', 'seg-231.m4s 4990ffd97e014b5e315671c26195744d', 'seg-232.m4s 4a2e62338083729cd114ddcf4685e00b']
        bad_checksums = ['seg-221.m4s c59b6068f8e29144a8843dae91417a46', 'seg-222.m4s d303ee4ea9b83b23bd8ef575ba91e0c9', 'seg-224.m4s fd938e0661353df437cf71297f614e79', 'seg-223.m4s 41caab57470a3696c106f7edd0e79ad5', 'seg-225.m4s f35f8f20db85b49abbd4204ba767d710', 'seg-226.m4s 10061ed9b33de483c5757d075e8c4eba', 'seg-227.m4s d58560ecc2d37039ab190c3f1be4aed7', 'seg-228.m4s ba4 2fb9edf72c11f92395b646baa74d', 'seg-229.m4s ee2dd1ee204d471bac4764a1f611c973', 'seg-230.m4s 9af2ec530ddf9feeea9241dd7da9ce21', 'seg-233.m4s fc5d352bbedd7327b00e034a5f33f79c', 'seg-231.m4s 4990ffd97e014b5e315671c26195744d', 'seg-232.m4s 4a2e62338083729cd114ddcf4685e00b']
        self.fd_device.source_mdsums = checksums
        self.fd_device.create_checksums_files = MagicMock(return_value=checksums)
        status = self.fd_device.compare_checksums_files('/tmp/tmpb8y1qgwb')
        self.assertEqual(status, 0)
        self.fd_device.create_checksums_files = MagicMock(return_value=bad_checksums)
        status = self.fd_device.compare_checksums_files('/tmp/tmpb8y1qgwb')
        self.assertEqual(status, 1)

    @patch('actions.fd_devices.os.walk', return_value=[('./a', [], ['1.txt', '2.txt', '3.txt']), 
            ('./b', [], ['4.txt', '5.txt', '6.txt']), ('.', ['a', 'b'], ['a.txt'])]) 
    @patch('actions.fd_devices.os.remove', side_effect=[None] * 7 + [OSError('OS ERROR')] + [None] *7)
    @patch('actions.fd_devices.os.rmdir', side_effect=[None] * 3 + [OSError('RMDIR ERROR')])
    def test_delete_all(self, mock_rmdir, mock_remove, mock_walk):
        status = self.fd_device.delete_all(directory='/foo/bar')
        self.assertEqual(status, 0)

        status = self.fd_device.delete_all(directory='/foo/bar')
        self.assertEqual(status, 1)

        status = self.fd_device.delete_all(directory='/foo/bar')
        self.assertEqual(status, 1)

        print(mock_remove.mock_calls)
        print(mock_rmdir.mock_calls)

    @patch.multiple('actions.fd_devices.logging', info=DEFAULT, error=DEFAULT)
    #@patch('actions.fd_devices.os.listdir', return_value = ['a.txt', 'b.txt', 'c.txt']) 
    @patch.multiple('actions.fd_devices.os', listdir=DEFAULT, remove=DEFAULT, rmdir=DEFAULT)
    def test_delete_ignored(self, listdir, remove, rmdir, info, error):
        listdir.return_value = return_value = ['a.txt', 'b.txt', 'c.txt']
        self.fd_device.ignore_files = ['a.txt']
        fd_devices.os.path.isfile = MagicMock(return_value=True)
        fd_devices.os.path.isdir = MagicMock(return_value=False)
        status = self.fd_device.delete_ignored(directory='/foo/bar')
        self.assertEqual(status, 0)
        #fd_devices.os.remove.assert_called_with('/foo/bar/a.txt')

        self.fd_device.ignore_files = ['a.txt']
        fd_devices.os.path.isfile = MagicMock(return_value=True)
        fd_devices.os.path.isdir = MagicMock(return_value=False)
        remove.side_effect=OSError()
        status = self.fd_device.delete_ignored(directory='/foo/bar')
        self.assertEqual(status, 1)

        rmdir.side_effect=OSError()
        self.fd_device.ignore_files = ['a.txt']
        fd_devices.os.path.isfile = MagicMock(return_value=False)
        fd_devices.os.path.isdir = MagicMock(return_value=True)
        status = self.fd_device.delete_ignored(directory='/foo/bar')
        self.assertEqual(status, 1)

    @patch('actions.fd_devices.os.walk', return_value=[('./a', [], ['1.txt', '2.txt', '3.txt']), 
            ('./b', [], ['4.txt', '5.txt', '6.txt']), ('.', ['a', 'b'], ['a.txt'])])
    def test_count_files(self, mock_walk):
        fd_devices.os.path.isdir = MagicMock(return_value=True)
        #fd_devices.os.walk = MagicMock(return_value=[('./a', [], ['1.txt', '2.txt', '3.txt']), 
        #    ('./b', [], ['4.txt', '5.txt', '6.txt']), ('.', ['a', 'b'], ['a.txt'])])
        num_files = self.fd_device.count_files('/foo/bar')
        self.assertEqual(num_files, 7)
        mock_walk.assert_called()


    @patch('actions.fd_devices.os.path.exists', return_value=False)
    @patch('actions.fd_devices.os.makedirs', side_effect=OSError())
    @patch('actions.fd_devices.logging.info')
    def test_makedirs(self, mock_info, mock_makedirs, mock_exists):
        dest = '/foo/bar/baz'
        self.fd_device.makedirs(dest)
        mock_exists.assert_called()
        mock_makedirs.assert_called_with(dest)
        mock_info.assert_called()


    def test_calculate_and_emit(self):
        def get_emit(x):
            self.x = x
        self.fd_device.emit = lambda x: get_emit(x)
        self.fd_device.calculate_and_emit(10, 100)
        self.assertEqual(self.x, 10)
        self.fd_device.calculate_and_emit(10, 100, adj=50, pc=50)
        self.assertEqual(self.x, 55)
    
    @patch('actions.fd_devices.os.walk', return_value=[('/tmp/sda/a', [], ['1.txt', '2.txt', '3.txt']), 
            ('/tmp/sda/b', [], ['4.txt', '5.txt', '6.txt']), ('/tmp/sda', ['a', 'b'], ['a.txt'])])
    @patch('actions.fd_devices.shutil.copy')
    def test_copy_files(self, mock_copy, mock_walk):
        self.fd_device.source_dir = '/tmp/sda'
        self.fd_device.dest_dir = '/tmp/sdb'
        self.fd_device.count_files = MagicMock(return_value=10)
        self.fd_device.makedirs = MagicMock()
        self.fd_device.calculate_and_emit = MagicMock()
        self.fd_device.checksums = MagicMock(return_value=True)

        status = self.fd_device.copy_files()
        mock_walk.assert_called_with(self.fd_device.source_dir)
        self.assertEqual(status, 0)
        self.fd_device.calculate_and_emit.assert_called()

        self.assertEqual(self.fd_device.calculate_and_emit.call_count, 7)

    #@patch('actions.fd_devices.subprocess.check_call', side_effect=[0, 0, 0, subprocess.CalledProcessError('CalledProcessError'), subprocess.TimeoutExpired('TimeoutExpired'), OSError('OS Error')])
    @patch('actions.fd_devices.subprocess.check_call', side_effect=[0, 0, 0, OSError('OS Error')])
    @patch('actions.fd_devices.logging.info')
    def test_check_call(self, mock_info, mock_check_call):
        cmd = shlex.split('ls -l')
        status = self.fd_device.check_call(cmd)
        self.assertEqual(status, 0)
        mock_check_call.assert_called_with(cmd, timeout=None, shell=False)

        #test with timeout 
        cmd = shlex.split('ls -l')
        status = self.fd_device.check_call(cmd, timeout=10)
        self.assertEqual(status, 0)
        mock_check_call.assert_called_with(cmd, timeout=10, shell=False)

        #test with timeout and shell
        cmd = shlex.split('ls -l')
        status = self.fd_device.check_call(cmd, timeout=10, shell=True)
        self.assertEqual(status, 0)
        mock_check_call.assert_called_with(cmd, timeout=10, shell=True)
        #test CalledProcesserError

        #fd_devices.subprocess.check_call = MagicMock(return_value=0, side_effect=fd_devices.subprocess.CalledProcessError('CalledProcessError')) 
        #cmd = shlex.split('ls -l')
        #status = self.fd_device.check_call(cmd)
        #self.assertEqual(status, 1)
        ##mock_check_call.assert_called_with(cmd, timeout=None, shell=False)
        #mock_info.assert_called_with(self.fd_device.device, 'CalledProcessError')
        #fd_devices.subprocess.check_call.assert_called_with(cmd, timeout=None, shell=False)
        #
        #fd_devices.subprocess.check_call = MagicMock(side_effect=subprocess.CalledProcessError(subprocess.TimeoutExpired('TimeoutExpired'))) #side_effect=[0, 0, 0, subprocess.CalledProcessError('CalledProcessError'), subprocess.TimeoutExpired('TimeoutExpired'), OSError('OS Error')])
        #cmd = shlex.split('ls -l')
        #status = self.fd_device.check_call(cmd)
        #self.assertEqual(status, 1)
        ##mock_check_call.assert_called_with(cmd, timeout=None, shell=False)
        #mock_info.assert_called_with(self.fd_device.device, 'TimeoutExpired')
        #fd_devices.subprocess.check_call.assert_called_with(cmd, timeout=None, shell=False)

        cmd = shlex.split('ls -l')
        status = self.fd_device.check_call(cmd)
        self.assertEqual(status, 1)
        mock_check_call.assert_called_with(cmd, timeout=None, shell=False)
        mock_info.assert_called_with(f'{self.fd_device.device}: OS Error')

    @patch('actions.fd_devices.logging.info')
    def test_format_device(self, mock_info):
        fd_devices.parted.getDevice = MagicMock()
        fd_devices.parted.freshDisk = MagicMock()
        self.fd_device.check_mountpoint = MagicMock()
        self.fd_device.check_call = MagicMock(return_value=0)
        status = self.fd_device.format_device()
        self.assertEqual(status, 0)

    @patch('actions.fd_devices.logging.info')
    def test_check_mountpoint(self, mock_info):
        mount_dir = '/foo/bar'
        device = '/dev/sdf'
        self.fd_device.check_call = MagicMock(return_value=0)
        status = self.fd_device.check_mountpoint(mount_dir=mount_dir, device=device)
        self.assertIn(call(['umount', '/foo/bar'], timeout=30), self.fd_device.check_call.mock_calls)
        self.assertIn(call(['mountpoint', '-q', '/foo/bar'], timeout=30), self.fd_device.check_call.mock_calls)
        self.assertEqual(status, 0)

        status = self.fd_device.check_mountpoint(device=device)
        self.assertEqual(status, 0)
        self.assertIn(call(['umount', '/dev/sdf'], timeout=30), self.fd_device.check_call.mock_calls)
        
    
    @patch('actions.fd_devices.logging.info')
    def test_copy_files_to_device(self, mock_info):
        self.fd_device.device = '/dev/sda'
        self.fd_device.mount_device = MagicMock(return_value=('/tmp/tmpdir', 0))
        self.fd_device.format_device = MagicMock(return_value=0)
        self.fd_device.delete_all = MagicMock(return_value=0)
        self.fd_device.copy_files = MagicMock(return_value=0)
        self.fd_device.check_mountpoint = MagicMock(return_value=0)
        self.fd_device.checksums = True
        self.fd_device.compare_checksums_files = MagicMock(return_value=0)
        self.fd_device.remove_temp_dir = MagicMock(return_value=0)

        status = self.fd_device.copy_files_to_device()
        self.assertEqual(status, 0)

        self.fd_device.check_mountpoint = MagicMock(return_value=32)
        status = self.fd_device.copy_files_to_device()
        self.assertEqual(status, 0)

        self.fd_device.mount_device = MagicMock(return_value=('/tmp/tmpdir', 1))
        self.fd_device.format_device = MagicMock(return_value=1)
        status = self.fd_device.copy_files_to_device()
        self.assertEqual(status, 1)

    @patch('actions.fd_devices.os.rmdir')
    def test_remove_temp_dir(self, mock_rmdir):
        self.fd_device.device = '/dev/sda'
        self.fd_device.device_dir = '/foo/bar'
        status = self.fd_device.remove_temp_dir()
        self.assertEqual(status, 0)
        mock_rmdir.assert_called_with('/foo/bar')
        

    def test_prepare_to_copy(self):
        self.fd_device.mount_device = MagicMock(return_value=('/tmp/tmpdir', 0))
        self.fd_device.delete_ignored = MagicMock(return_value=0)
        self.fd_device.create_checksums_files = MagicMock(return_value=0)
        status = self.fd_device.prepare_to_copy(checksums=True)
        self.assertEqual(status, 0)

    def test_emit(self):
        self.fd_device.hub = '/dev/sda'
        self.fd_device.hub_coordinates = '00'
        self.fd_device.progress_callback = MagicMock()
        self.fd_device.progress_callback.emit = MagicMock()
        self.fd_device.emit(50)
        self.fd_device.progress_callback.emit.assert_called_with((50, '/dev/sda', '00'))


    @patch('actions.fd_devices.logging.info')
    def test_copy(self, mock_info):
        self.fd_device.copy_files_to_device = MagicMock(return_value='results123')
        self.fd_device.check_mountpoint = MagicMock(return_value=0)
        self.fd_device.checksums = False
        source_device = '/dev/sda'
        source_dir = '/foo/bar'
        results = self.fd_device.copy(source_device, source_dir)
        self.assertEqual(results, 'results123')

class MailTests(unittest.TestCase):
    @patch('actions.mail.smtplib.SMTP', return_value=MagicMock())
    def setUp(self, mock_SMTP):
        self.mail = Mail()
        mock_SMTP.assert_called()

    def test_compose_mail(self):
        with patch('actions.mail.open', mock_open(read_data='Atachment Text')):
            self.mail.compose_mail('This is a message', 'foo@bar', ['baz@bar', 'baz2@bar'], subject='This is the subject')
        self.assertIsInstance(self.mail.msg, MIMEMultipart)
        self.assertEqual(self.mail.msg['From'], 'foo@bar')
        self.assertEqual(self.mail.msg['To'], 'baz@bar, baz2@bar')
        self.assertEqual(self.mail.msg['Subject'], 'This is the subject')


    @patch('actions.mail.logging')
    def test_send_mail(self, mock_logging): 
        self.mail.server.sendmail = MagicMock()
        self.mail.msg = MagicMock()
        self.mail.msg.as_string = MagicMock(return_value='Message')
        self.mail.disconnect = MagicMock()
        self.mail.send_mail('foo@bar', ['baz1@foobar', 'baz2@foobar'])
        mock_logging.assert_not_called()
        self.mail.server.sendmail.assert_called_with('foo@bar', ['baz1@foobar', 'baz2@foobar'], 'Message')
        

    def test_connect(self):
        self.mail.server = MagicMock()
        self.mail.connect()
        self.mail.server.connenct.assert_called()


    def test_connect(self):
        self.mail.server = MagicMock()
        self.mail.disconnect()
        self.mail.server.quit.assert_called()


if __name__ == '__main__':
    unittest.main()
