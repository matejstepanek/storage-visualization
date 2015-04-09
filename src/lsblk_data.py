'''
Created: 2015

@author: mstepane@redhat.com

Collecting data from lsblk command output.
'''

import utils
import subprocess


class LsblkData:
    """Collecting data from lsblk command output.
    """
    
    def get_lsblk_elements(self, pvs):
        """Gathers data from lsblk command output.
        
        Returns:
        - lsblk_with_pvs - list of lsblk elements connected with pvs  
        - lsblk_lvm      - list of lsblk elements of lvm type  
        
        Each item in the list is a dictionary with these keys: 
        uuid, name, type, mountpoint, fstype, size, parents, children,
        encrypted, label, fsoccupied.
        
        Label is structured: name, content, size, type.
        
        Devices are connected into the dependency tree by keys parents and children. 
        """
        
        # Run lsblk command.
        lsblk = subprocess.check_output(['lsblk', '-Pnb', '--output',
                                    'UUID,NAME,TYPE,MOUNTPOINT,FSTYPE,SIZE'])
        # From lsblk make list of strings (rows). Without the last empty row. 
        devices_strings = lsblk.split('\n')[:-1]
        
        keys = ['uuid','name','type','mountpoint','fstype','size']
        devices = [dict(zip(keys, dev.split())) for dev in devices_strings]
        
        self.process_block_devices(devices, keys)
         
        # Filter devices - preserve only devices that are interesting for us
        devices = [dev for dev in devices if dev['type'] not in ['rom']]
        
        self.add_crypt_to_chidren(devices)
        self.add_partitions_to_children(devices) 
        self.add_raid_to_children(devices)
        
        devices = self.merge_raid_devices(devices)
        devices = self.remove_duplicates(devices)
        
        self.add_pvs_to_children(devices, pvs)        
        lsblk_with_pvs = self.skip_encryption(devices+pvs)
                
        for elem in lsblk_with_pvs:
            if elem['type'] != 'lvm':
                utils.set_label(elem)
            
        return lsblk_with_pvs

    def process_block_devices(self, devices, keys):     
        """Sets and modifies some values of attributes.
        """
        
        for dev in devices:     
            # Remove name of the key from value.
            for key in keys:
                dev[key] = dev[key].split('"')[1]
            # Remark: There is a problem with the uuid. 
            # Eg. disk has no one at the beggining. Thats why the name is added.
            dev['uuid'] = ''.join([dev['name'], '@', dev['uuid']])
            dev['size'] = int(dev['size'])
            dev['parents'] = []
            dev['children'] = []
            
            if dev['fstype'].startswith('crypt'):
                dev['encrypted'] = True
            else:
                dev['encrypted'] = False
            
            mounted = self.get_mounted()
            if dev['mountpoint'] and dev['mountpoint'] in mounted.keys():
                dev['fsoccupied'] = mounted[dev['mountpoint']]
            else:
                dev['fsoccupied'] = -1
                
    def get_mounted(self):
        """Returns dictionary with mounted file systems.
    
        Key:   mount point
        Value: percentage of occupied space (float between 0 and 100)
        """
    
        # Run df command.
        lsblk = subprocess.check_output(['df', '-BKB'])
        # From df make list of strings (rows). 
        strings = lsblk.split('\n')[1:-1]
        
        mounted = {}
        
        for s in strings:
            mount_point = s.split()[-1]
            occupied = float(s.split()[-2][:-1])
            mounted[mount_point] = occupied
            
        return mounted
    
    def add_crypt_to_chidren(self, devices):
        """Includes encrypted devices among children of their parent devices.
        
        Assumption: specific order of rows in lsblk output.
        """
        
        for i,dev in enumerate(devices):    
            if dev['type'] == 'crypt':
                parent = devices[i-1]
                utils.connect(parent, dev)
                
    def add_partitions_to_children(self, devices):
        """Includes disk partitions among children of their parent devices.
        
        Assumption: specific order of rows in lsblk output.
        """
        
        for i,dev in enumerate(devices):        
            if dev['type'] == ('disk' or 'loop'):
                if dev['fstype'].startswith('crypt'):
                    parent = devices[i+1]
                else:
                    parent = dev
            elif dev['type'] == 'part':  
                utils.connect(parent, dev)
                
    def add_raid_to_children(self, devices):
        """Includes md raid devices among children of their parent devices.
        
        Assumption: specific order of rows in lsblk output.
        """
         
        rev_devices = reversed(devices)
        
        for dev in rev_devices:                    
            if dev['type'].startswith('raid'):
                parent = next(rev_devices)
                utils.connect(parent, dev)
                
    def merge_raid_devices(self, devices):
        """Merges multiple rows (from lsblk output) for one md raid device. 
        Preserves all information (all parent devices).
        """
        
        raids = [dev for dev in devices if dev['type'].startswith('raid')]
        copy_raids = list(raids)
        result = []
        checked = []
        
        for raid in raids:
            if raid['uuid'] not in checked:
                for r in copy_raids:
                    if raid['uuid'] == r['uuid']:
                        for p_uuid in r['parents']:
                            parent = utils.get_by_uuid(p_uuid, devices)
                            utils.connect(parent, raid)
                result.append(raid)
                checked.append(raid['uuid'])
                    
        devices = [dev for dev in devices if not dev['type'].startswith('raid')]
        return devices + result
        
    def remove_duplicates(self, devices):
        """Removes duplicates from list of dicts.
        """
        
        unique = []
        result = []
        
        for dev in devices:
            if dev['uuid'] not in unique:                
                unique.append(dev['uuid'])
                result.append(dev)
                
        return result
            
    def add_pvs_to_children(self, devices, pvs):
        """Connects devices with physical volumes built on them.
        """
        
        for dev in devices:
            match = False
            
            if dev['type'] != 'lvm':
                
                short_uuid = dev['uuid'].split('@')[1]
                
                # Compares uuid of devices from pvs and lsblk
                for pv in pvs:
                    if short_uuid == pv['uuid'].split('@')[1]:
                        utils.connect(dev,pv)   
                        match = True 
                        break
                
                if not match:
                    # When you create PV on loop, loop sometimes hasn't got 
                    # an uuid yet. Therefore we have to compare the names.
                    for pv in pvs:
                        if pv['name'].split('/')[-1] == dev['name']:
                            utils.connect(dev,pv)
                            break
            elif not match:
                
                # Tests lvs whether they are pv. Compares names.
                for pv in pvs:
                    if pv['name'].count('/') > 2:
                        # LVM device in lsblk output has this form:
                        # VGname-LVname where every dash in VGname or LVname
                        # is doubled.                    
                        pv_name = pv['name'].replace('-','--')                        
                        vg_part = pv_name.split('/')[-2]
                        pv_part = pv_name.split('/')[-1]                                
                        pv_name = ''.join([vg_part, '-', pv_part])
                        if pv_name == dev['name']:
                            utils.connect(dev,pv)
                            break
                
    def skip_encryption(self, elements):
        """Returns elements without encryption. Attributes of encryption 
        (mountpoint, fstype, ...) are given to the parent element.
        """
        
        encryptions = []
        copy_elems = list(elements)
        
        for elem in elements:
            if elem['encrypted'] and elem['children']:
                crypt = utils.get_by_uuid(elem['children'][0],copy_elems)
                elem['mountpoint'] = crypt['mountpoint']
                elem['fstype'] = crypt['fstype']
                elem['children'] = crypt['children']
                elem['fsoccupied'] = crypt['fsoccupied']
                encryptions.append(crypt['uuid'])
                
                for child_uuid in elem['children']:
                    child = utils.get_by_uuid(child_uuid, elements)
                    child['parents'].remove(crypt['uuid'])
                    child['parents'].append(elem['uuid'])
                    
            elif elem['encrypted']:
                elem['fstype'] = ''
                
        return [elem for elem in elements if elem['uuid'] not in encryptions]

