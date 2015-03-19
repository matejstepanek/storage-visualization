#!/usr/bin/python
'''
Created: 2014 - 2015

@author: mstepane

Gathering data by these commands: lsblk, df, pvs, vgs, lvs.

Instructions when running in eclipse:
Add this line to the end of /etc/sudoers ('username' replace with your username)
username ALL = NOPASSWD: ALL 
And comment this line (if it's present) in /etc/sudoers
Defaults    requiretty
It enables you to run sudo commands without entering the password. 
'''

import subprocess
from itertools import groupby


def get_by_uuid(uuid, elements):
    """From the list of storage elements returns an element with a given uuid.
    """
    match = None
    for elem in elements:
        if elem['uuid'] == uuid:
            match = elem
            break
    return match

def get_by_name(name, elements):
    """From the list of elements returns an element with a given name.
    """
    match = None
    for elem in elements:
        if elem['name'] == name:
            match = elem
            break
    return match

def get_mounted():
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


class Elements:
    """
    Functions for getting information about storage elements in the system.
    Commands df, lsblk, lvs, vgs, pvs are used.
    
    Process:
    - get pvs with labels
    - get vgs with labels
    
    - get lsblk elements connected
    - connect pvs to lsblk elements
    - give labels
    - return devices_pvs (without vgs and lvs)
    
    - get lvs (with help of lsblk lvm_devices)
    
    - set dependencies among pvs, vgs and lvs
    """          
    def get_data(self):
        """Returns storage elements connected into tree structure.
        """
        pvs = self.get_pvs()
        vgs = self.get_vgs()  
        
        (devices_pvs, lvm_devices) = self.get_block_devices(pvs)
        (lvs, _internal_lvs) = self.get_lvs(lvm_devices, pvs)
        
        self.set_dependencies_lvm(pvs, vgs, lvs)
        
        all_elems = devices_pvs + vgs + lvs
        disks_loops = [d for d in devices_pvs if d['type'] in ['disk', 'loop']]
        
        return (all_elems, pvs, vgs, lvs, disks_loops)
      
    def get_block_devices(self, pvs):
        """Returns list of block devices from lsblk command output.
        These data are combined with information about lvm elements (pvs, vgs, 
        lvs commands) to get the whole picture.
        
        Each item in the list is a dictionary with these keys: 
        uuid, name, type, mountpoint, fstype, size, parents, children,
        encrypted, label.
        
        Label is structured: name, content, size, type.
        
        Devices are connected into the dependency tree by keys parents and children. 
        Remark: can return some identical devices more times (eg. md raid)
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
        devices_pvs = self.skip_encryption(devices+pvs)
        (devices_pvs, lvm_devices) = self.separate_lvm_devices(devices_pvs)
        for dev in devices_pvs:
            self.set_label(dev)
            
        return (devices_pvs, lvm_devices)

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
    
    def add_crypt_to_chidren(self, devices):
        """Includes encrypted devices among children of their parent devices.
        
        Assumption: specific order of rows in lsblk output.
        """ 
        for i,dev in enumerate(devices):    
            if dev['type'] == 'crypt':
                parent = devices[i-1]
                self.connect(parent, dev)
                
    def connect(self, parent, child):
        """Connects parent and child elements.
        """
        if child['uuid'] not in parent['children']:
            parent['children'].append(child['uuid'])
        if parent['uuid'] not in child['parents']:
            child['parents'].append(parent['uuid'])
        
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
                self.connect(parent, dev)
                
    def add_raid_to_children(self, devices):
        """Includes md raid devices among children of their parent devices.
        
        Assumption: specific order of rows in lsblk output.
        """ 
        rev_devices = reversed(devices)
        for dev in rev_devices:                    
            if dev['type'].startswith('raid'):
                parent = next(rev_devices)
                self.connect(parent, dev)
                
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
                            parent = get_by_uuid(p_uuid, devices)
                            self.connect(parent, raid)
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
                        self.connect(dev,pv)   
                        match = True 
                        break
                if not match:
                    # When you create PV on loop, loop sometimes hasn't got 
                    # an uuid yet. Therefore we have to compare the names.
                    for pv in pvs:
                        if pv['name'].split('/')[-1] == dev['name']:
                            self.connect(dev,pv)
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
                            self.connect(dev,pv)
                            break
                
    def skip_encryption(self, elements):
        """Returns elements without encryption. Attributes of encryption 
        (mountpoint, fstype, ...) are given to the parent element.
        """
        encryptions = []
        copy_elems = list(elements)
        for elem in elements:
            if elem['encrypted'] and elem['children']:
                crypt = get_by_uuid(elem['children'][0],copy_elems)
                elem['mountpoint'] = crypt['mountpoint']
                elem['fstype'] = crypt['fstype']
                elem['children'] = crypt['children']
                encryptions.append(crypt['uuid'])
                for child_uuid in elem['children']:
                    child = get_by_uuid(child_uuid, elements)
                    child['parents'].remove(crypt['uuid'])
                    child['parents'].append(elem['uuid'])
            elif elem['encrypted']:
                elem['fstype'] = ''
        return [elem for elem in elements if elem['uuid'] not in encryptions]
                 
    def separate_lvm_devices(self, devices):
        """Divides devices into 2 lists: 
        1) disk, loops, partitions, md raids, multipath devices
        2) lvm devices (i.e. logical volumes) 
        """ 
        lvm_devices = []
        copy_devices = devices[:]
        for dev in copy_devices:
            if dev['type'] == 'lvm':                      
                devices.remove(dev)
                if dev not in lvm_devices:
                    lvm_devices.append(dev)
        return (devices, lvm_devices)

    def make_readable(self, size):
        """Given a size in bytes returns a human readable equivalent.
        """
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
       
        i = 0
        while size >= 1000 and i < len(suffixes)-1:
            size /= 1000.0
            i += 1
        
        if size == 0:
            size_str = '0'    
        elif size < 10:
            size_str = ('%.1f' % size).rstrip('0').rstrip('.')
        else:
            size_str = '%.0f' % size
        
        readable = '%s %s' % (size_str, suffixes[i])
        return readable
    
    def set_label(self, elem, internal_lvs = None):
        """Sets a label of a storage element.
        
        The label contains information about element's:
            1) name
            2) content - file system and mountpoint
            3) size - also available space size and percentage of occupied space
            4) type
        """
        typ = elem['type']
        elem['label'] = {}
        
        elem['label']['name'] = elem['name'].split('/')[-1]
        
        elem['label']['content'] = elem['fstype']
        if elem['mountpoint']:
            elem['label']['content'] += ' - mounted in %s' %elem['mountpoint']
            
        elem['label']['size'] = self.make_readable(elem['size'])
        free = False
        if typ == 'vg': 
            free = elem['vg_free']
            percent =  (1 - float(elem['vg_free'])/elem['size']) * 100
        elif typ == 'lv' and elem['data_percent'] != '':
            percent = elem['data_percent']
            free = elem['size'] * (100-percent) / 100
        elif elem['mountpoint']:
            mounted = get_mounted()
            mpoint = elem['mountpoint']
            if mpoint in mounted.keys():
                percent = mounted[elem['mountpoint']]
                free = elem['size'] * (100-percent) / 100
        if free:
            elem['label']['size'] += ' - %s available (%.1f %% occupied)' %(
                                            self.make_readable(free), percent)
        
        elem['label']['type'] = {}
        if typ == 'disk':
            elem['label']['type']['short'] = 'Disk'
            elem['label']['type']['long']  = 'Disk'                
        elif typ == 'loop':
            elem['label']['type']['short'] = 'Loop device'
            elem['label']['type']['long']  = 'Loop device'    
        elif typ == 'part':
            elem['label']['type']['short'] = 'Partition'
            elem['label']['type']['long']  = 'Partition'
        elif typ.startswith('raid'):
            elem['label']['type']['short'] = typ.capitalize()
            elem['label']['type']['long']  = typ.capitalize()
        elif typ == 'pv':
            elem['label']['type']['short'] = 'PV'
            elem['label']['type']['long']  = 'Physical volume'
        elif typ == 'vg':
            elem['label']['type']['short'] = 'VG'
            elem['label']['type']['long']  = 'Volume group'
        elif typ == 'lv':
            type_lv = elem['segtype']
            if type_lv == 'cache':
                elem['label']['type']['short'] = 'Cached LV'
                elem['label']['type']['long']  = 'Logical volume with cache %s' %elem['pool_lv']
            elif type_lv == 'cache-pool':
                elem['label']['type']['short'] = 'Cache pool'
                elem['label']['type']['long']  = 'Cache pool'
            elif type_lv == 'thin-pool':
                elem['label']['type']['short'] = 'Thin pool'
                elem['label']['type']['long']  = 'Thin pool'
                is_raid = self.check_tdata(elem, internal_lvs)
                if is_raid:
                    elem['label']['type']['short'] += ', ' + is_raid
                    elem['label']['type']['long'] += ', ' + is_raid
            elif type_lv == 'thin':
                if elem['origin']:
                    elem['label']['type']['short'] = 'Thin snap.'
                    elem['label']['type']['long']  = 'Thin snapshot of %s' %elem['origin']
                else:    
                    elem['label']['type']['short'] = 'Thin LV'
                    elem['label']['type']['long']  = 'Thin logical volume' 
            elif elem['origin']:
                elem['label']['type']['short'] = 'Snapshot'
                elem['label']['type']['long']  = 'Snapshot of %s'%elem['origin']
            else:
                elem['label']['type']['short'] = 'LV'
                elem['label']['type']['long']  = 'Logical volume'
            
            if type_lv.startswith('raid'):
                    elem['label']['type']['short'] += ', ' + type_lv
                    elem['label']['type']['long'] += ', ' + type_lv 
        else:
            elem['label'] = [typ.capitalize(), typ.capitalize()]
                            
        if elem['encrypted']:
            elem['label']['type']['long'] += ', encrypted'
                
    def check_tdata(self, tpool, internal_lvs):
        """Checks if thin pool is lvm raid as well.
        """
        result = None
        key = '[%s_tdata]' %tpool['name']
        for lv in internal_lvs:
            if lv['name'] == key:
                if lv['segtype'].startswith('raid'):
                    result = lv['segtype']
        return result

    def get_pvs(self):
        """Returns list of physical volumes in system.
        
        Each item in the list is a dictionary with these keys: 
        uuid, name, type, mountpoint, fstype, size, parents, children, encrypted,
        label, vg_name.
        """  
        # Run pvs command.   
        pvs = subprocess.check_output(['sudo', 'pvs', '--units', 'b', 
                                       '--noheadings', '--separator', '@', '-o', 
                                       'pv_uuid,pv_name,vg_name,dev_size'])
        pvs = pvs.split('\n')[:-1]
        
        # If there is only one row in pvs, make a list from it.
        if isinstance(pvs, str):    
            pvs = [pvs]
            
        keys = ['uuid', 'name', 'vg_name', 'size']
        pvs = [dict(zip(keys, pv.split('@'))) for pv in pvs]
        
        for pv in pvs:
            self.process_lvm_element(pv)
            pv['type'] = 'pv'
            pv['uuid'] = pv['uuid'] + '@pv'
            self.set_label(pv)            
        return pvs
    
    def process_lvm_element(self, elem):
        """Prettifies attributes' values and sets some default values. 
        """
        elem['uuid'] = ''.join([elem['name'], '@', elem['uuid'].strip()])
        # Remove 'B' from the end of a size
        elem['size'] = int(elem['size'][:-1])  
        elem['mountpoint'] = ''
        elem['fstype'] = ''
        elem['parents'] = []
        elem['children'] = []
        elem['encrypted'] = False

    def get_vgs(self):
        """Returns list of volume groups in system.
        
        Each item in the list is a dictionary with these keys:
        uuid, name, type, mountpoint, fstype, size, parents, children, encrypted,
        label, vg_free.
        """
        # Run vgs command.
        vgs = subprocess.check_output(['sudo', 'vgs', '--units', 'b',
                                       '--noheadings', '--separator', '@', '-o', 
                'vg_uuid,vg_name,vg_size,vg_free'])
        vgs = vgs.split('\n')[:-1]
        
        # If there is only one row in vgs, make a list from it.
        if isinstance(vgs, str):    
            vgs = [vgs]
            
        keys = ['uuid','name','size','vg_free']    
        vgs = [dict(zip(keys, vg.split('@'))) for vg in vgs]
        
        for vg in vgs:
            self.process_lvm_element(vg) 
            vg['type'] = 'vg'
            vg['vg_free'] = vg['vg_free'][:-1]
            vg['vg_free'] = int(vg['vg_free'])
            self.set_label(vg) 
        return vgs

    def get_lvs(self, lvm_devices, pvs):
        """Returns list of logical volumes in system.
        
        Each item in the list is a dictionary with these keys:   
        uuid, name, type, mountpoint, fstype, size, parents, children, encrypted,
        label, vg_name, origin (for snapshots), segtype, pool_lv, data_percent,
        is_origin.
        """
        # Run lvs command.
        lvs = subprocess.check_output(['sudo', 'lvs', '-a', '--units', 'b', 
                                       '--noheadings', '--separator', '@', '-o',
        'lv_uuid,lv_name,vg_name,origin,lv_size,segtype,pool_lv,data_percent'])  
        lvs = lvs.split('\n')[:-1]
        
        # If there is only one row in lvs, make a list from it.
        if isinstance(lvs, str):    
            lvs = [lvs]
            
        keys = ['uuid','name','vg_name','origin','size','segtype','pool_lv',
                'data_percent']        
        lvs = [dict(zip(keys, lv.split('@'))) for lv in lvs]
            
        for lv in lvs:
            self.process_lvm_element(lv)
            lv['type'] = 'lv'
            lv['is_origin'] = False
            if lv['data_percent']:
                lv['data_percent'] = float(lv['data_percent'].replace(',', '.'))
            
            dev = self.get_lv_from_devices(lv, lvm_devices)
            # Adds information from lsblk command.
            if dev:
                lv['mountpoint'] = dev['mountpoint']
                lv['fstype'] = dev['fstype']
                lv['encrypted'] = dev['encrypted']
                lv['children'] = dev['children']
                for ch_uuid in dev['children']:
                    ch = get_by_uuid(ch_uuid, pvs)
                    ch['parents'] = [lv['uuid']]
                    
        standard_not_unique = [l for l in lvs if not l['name'].startswith('[')]
        standard = [key for key,_group in groupby(sorted(standard_not_unique))]
        internal = [lv for lv in lvs if lv['name'].startswith('[')]
    
        for lv in lvs:
            if lv['origin']:
                if lv['segtype'] != 'cache':
                    # Sets atributte 'is_origin' (i.e. origin of a snapshot)
                    origin = get_by_name(lv['origin'], standard)
                    if origin:
                        origin['is_origin'] = True
            if lv['segtype'] == 'cache':
                cache_pool = get_by_name(lv['pool_lv'], internal)
                standard.append(cache_pool)
            self.set_label(lv, internal)
        
        return (standard, internal)
    
    def get_lv_from_devices(self, lv, lvm_devices):
        """Given logical volume returns corresponding device from lsblk output.
        """
        result = None
        
        # LVM device in lsblk output has this form: VGname-LVname
        # where every dash in VGname or LVname is doubled.  
        vg_name = lv['vg_name'].replace('-','--')
        lv_name = lv['name'].replace('-','--')
        
        key = ''.join([vg_name, '-', lv_name])
        for dev in lvm_devices:
            if dev['name'] == key:
                result = dev
                break
        return result
                
    def set_dependencies_lvm(self, pvs, vgs, lvs):
        """Records dependencies between volume group and physical/logical volumes.
        """ 
        # Connect pv to vg
        for pv in pvs:
            for vg in vgs:
                if vg['name'] == pv['vg_name']:
                    self.connect(pv, vg)
                    break
                        
        for lv in lvs:                
            if lv['pool_lv'] and lv['segtype'] != 'cache':
                # Connect thin lv to its pool
                for lv2 in lvs:
                    if lv['pool_lv'] == lv2['name']:
                        parent = lv2
                        break
                self.connect(parent, lv)
            else:
                # Connect lv to vg
                for vg in vgs:
                    if lv['vg_name'] == vg['name']:
                        self.connect(vg, lv)
                        break
                     
#################################### TESTING ###################################
if __name__ == '__main__': 
    elems = Elements()
    (all_elems, pvs, vgs, lvs, disks_loops) = elems.get_data()
    print '-----------------------------------------------------------------'
    for x in all_elems:
        print x['name'], x['uuid']
        
        