'''
Created: 2015

@author: mstepane@redhat.com

Collecting data from lsblk command output.
'''

import subprocess

import utils


def get_lsblk_elements(pvs):
    """Gathers data from lsblk command output.
    
    Returns:
    - lsblk_with_pvs - list of lsblk elements (devices) connected with pvs  
    - lsblk_lvm      - list of lsblk elements (devices) of lvm type  
    
    Each item in the list is a dictionary with these keys: 
    uuid, name, type, mountpoint, fstype, size, parents, children, encrypted,
    label, fsoccupied.
    
    Label is structured: name, content, size, type.
    
    Elements are connected into the dependency tree by keys parents and children. 
    """
    
    lsblk_output = subprocess.check_output(['lsblk', '-Pnb', '--output',
                                'UUID,NAME,TYPE,MOUNTPOINT,FSTYPE,SIZE'])
    # From lsblk make list of strings (rows). Without the last empty row. 
    lsblk_list = lsblk_output.split('\n')[:-1]
    
    keys = ['uuid','name','type','mountpoint','fstype','size']
    devices = [dict(zip(keys, dev.split())) for dev in lsblk_list]
    
    process_block_devices(devices, keys)
     
    # Preserve only devices that are interesting for us
    devices = [dev for dev in devices if dev['type'] not in ['rom']]
    
    lsblk_with_pvs = build_dependency_tree(devices, pvs)
            
    for elem in lsblk_with_pvs:
        if elem['type'] != 'lvm':
            utils.set_label(elem)

    return lsblk_with_pvs


def process_block_devices(devices, keys):     
    """Sets and modifies some values of keys.
    """
    
    for dev in devices:     
        # Remove name of the key from value.
        for key in keys:
            dev[key] = dev[key].split('"')[1]
        # Remark: There is a problem with an uuid.
        # Eg. disk has no one at the beggining. Thats why the name is added.
        dev['uuid'] = ''.join([dev['name'], '@', dev['uuid']])
        dev['size'] = int(dev['size'])
        dev['parents'] = []
        dev['children'] = []
        
        if dev['fstype'].startswith('crypt'):
            dev['encrypted'] = True
        else:
            dev['encrypted'] = False
        
        mounted = get_mounted()
        if dev['mountpoint'] and dev['mountpoint'] in mounted.keys():
            dev['fsoccupied'] = mounted[dev['mountpoint']]
        else:
            dev['fsoccupied'] = -1


def get_mounted():
    """Returns dictionary with mounted file systems.

    Key:   mount point
    Value: percentage of occupied space (float between 0 and 100)
    """

    lsblk = subprocess.check_output(['df', '-BKB'])
    strings = lsblk.split('\n')[1:-1]
    
    mounted = {}
    
    for s in strings:
        mount_point = s.split()[-1]
        occupied = float(s.split()[-2][:-1])
        mounted[mount_point] = occupied
        
    return mounted


def build_dependency_tree(devices, pvs):
    """Connects lsblk elements into a dependency tree.
    """
    
    add_crypt_to_chidren(devices)
    add_partitions_to_children(devices) 
    add_raid_to_children(devices)
    
    devices = merge_raid_devices(devices)
    
    devices = remove_duplicates(devices)
    
    add_pvs_to_children(devices, pvs)
          
    lsblk_with_pvs = skip_encryption(devices+pvs)
    
    return lsblk_with_pvs


def add_crypt_to_chidren(devices):
    """Includes encrypted devices among children of their parent devices.
    
    Assumption: specific order of rows in lsblk output.
    """
    
    for i,dev in enumerate(devices):
        if dev['type'] == 'crypt':
            parent = devices[i-1]
            utils.connect(parent, dev)
            

def add_partitions_to_children(devices):
    """Includes disk partitions among children of their parent devices.
    
    Assumption: specific order of rows in lsblk output.
    """
    
    loop_devices = []
    
    for dev in devices:
        
        if dev['type'] == 'disk':
            parent = dev
        
        elif dev['type'] == 'part':
            utils.connect(parent, dev)
            
        elif dev['type'] == 'loop':
            
            if loop_devices:
                recognize_partition_on_loop(dev, loop_devices)
            else:
                loop_devices.append(dev)


def recognize_partition_on_loop(dev, loop_devices):
    """Includes partition on loop device among children of it.
    
    Partition on loop device has type 'loop' in lsblk output, so we need
    to compare names to recognize it. Loop device and its partitions
    have the same 'number', for example: loop4 - loop4p1, loop4p2.    
    """
    
    previous = loop_devices[-1]
    
    if dev['name'][4] == previous['name'][4]:
        utils.connect(previous, dev)
        dev['type'] = 'part'
    else:
        loop_devices.append(dev)
            

def add_raid_to_children(devices):
    """Includes md raid devices among children of their parent devices.
    
    Assumption: specific order of rows in lsblk output.
    """
     
    rev_devices = reversed(devices)
    
    for dev in rev_devices:                    
        if dev['type'].startswith('raid'):
            parent = next(rev_devices)
            utils.connect(parent, dev)
            

def merge_raid_devices(devices):
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
    

def remove_duplicates(devices):
    """Removes duplicates from list of dicts.
    """
    
    unique = []
    result = []
    
    for dev in devices:
        
        if dev['uuid'] not in unique:                
            unique.append(dev['uuid'])
            result.append(dev)
            
    return result
        

def add_pvs_to_children(devices, pvs):
    """Connects devices with physical volumes built on them.
    """
    
    for device in devices:
        
        if device['type'] != 'lvm':
            add_pvs_on_not_lvs(device, pvs)
            
        else:
            add_pvs_on_lvs(device, pvs)


def add_pvs_on_not_lvs(device, pvs):
    """Tests element whether it is a physical volume.
    
    First compares uuids, then names. (When you create PV on loop,
    it sometimes hasn't got an uuid yet. Therefore we have to compare names.)
    """
    
    match = False
    short_uuid = device['uuid'].split('@')[1]
            
    for pv in pvs:
        
        if short_uuid == pv['uuid'].split('@')[1]:
            utils.connect(device,pv)   
            match = True 
            break
    
    if not match:
        
        for pv in pvs:
            
            if pv['name'].split('/')[-1] == device['name']:
                utils.connect(device,pv)
                break

def add_pvs_on_lvs(device, pvs):
    """Tests logical volumes whether they are pv. Compares names.
    
    LVM device in lsblk output has this form: VGname-LVname
    where every dash in VGname or LVname is doubled.
    """
    
    for pv in pvs:
        if pv['name'].count('/') > 2:
                                
            pv_name = pv['name'].replace('-','--')
                                          
            vg_part = pv_name.split('/')[-2]
            pv_part = pv_name.split('/')[-1]
            pv_name = ''.join([vg_part, '-', pv_part])
            
            if pv_name == device['name']:
                utils.connect(device,pv)
                break
            

def skip_encryption(elements):
    """Returns elements without encryptions. Attributes of encryption 
    (mountpoint, fstype, ...) are given to the parent element.
    """
    
    copy_elems = list(elements)
    encryptions = []
    
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

