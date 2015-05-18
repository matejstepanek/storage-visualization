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
    uuid, name, type, mountpoint, fstype, size, occupied, parents, children,
    encrypted, label.
    
    Label is structured: name, content, size, type.
    
    Elements are connected into the dependency tree by keys parents and children. 
    """
    
    lsblk_output = subprocess.check_output(['lsblk', '-Pnb', '--output',
                                'UUID,NAME,TYPE,MOUNTPOINT,FSTYPE,SIZE'])
    lsblk_list = lsblk_output.split('\n')[:-1]
    
    keys = ['uuid','name','type','mountpoint','fstype','size']
    devices = [dict(zip(keys, device.split())) for device in lsblk_list]
    
    process_block_devices(devices, keys)
     
    devices = [device for device in devices if device['type'] not in ['rom']]
    
    lsblk_with_pvs = build_dependency_tree(devices, pvs)
            
    for elem in lsblk_with_pvs:
        
        mounted = get_mounted()
        set_occupied_space(elem, lsblk_with_pvs, mounted)
        
        if elem['type'] != 'lvm':
            utils.set_label(elem)

    return lsblk_with_pvs


def process_block_devices(devices, keys):     
    """Sets and modifies some values of keys.
    """
        
    for device in devices:
        
        # Remove name of the key from value.
        for key in keys:
            device[key] = device[key].split('"')[1]
        
        # There is a problem with an uuid.
        # Eg. disk has no one at the beggining. Thats why the name is added.
        device['uuid'] = ''.join([device['name'], '@', device['uuid']])
        
        device['size'] = int(device['size'])
        
        device['parents'] = []
        device['children'] = []
        
        if device['fstype'].startswith('crypt'):
            device['encrypted'] = True
        else:
            device['encrypted'] = False
        

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


def set_occupied_space(device, devices, mounted):
    """Sets parameter 'occupied'.
    """

    if device['mountpoint'] and device['mountpoint'] in mounted.keys():
        device['occupied'] = mounted[device['mountpoint']]
    else:
        device['occupied'] = -1

    
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
    
    for i,device in enumerate(devices):
        
        if device['type'] == 'crypt':
            parent = devices[i-1]
            utils.connect(parent, device)
            
            parent['encrypted'] = True


def add_partitions_to_children(devices):
    """Includes disk partitions among children of their parent devices.
    
    Assumption: specific order of rows in lsblk output.
    """
    
    loop_devices = []
    
    for device in devices:
        
        if device['type'] == 'disk':
            parent = device
        
        elif device['type'] == 'part':
            utils.connect(parent, device)
            
        elif device['type'] == 'loop':
            
            if loop_devices:
                recognize_partition_on_loop(device, loop_devices)
            else:
                loop_devices.append(device)


def recognize_partition_on_loop(device, loop_devices):
    """Includes partition on loop device among children of it.
    
    Partition on loop device has type 'loop' in lsblk output, so we need
    to compare names to recognize it. Loop device and its partitions
    have the same 'number', for example: loop4 - loop4p1, loop4p2.    
    """
    
    previous = loop_devices[-1]
    
    if device['name'][4] == previous['name'][4]:
        utils.connect(previous, device)
        device['type'] = 'part'
    else:
        loop_devices.append(device)
            

def add_raid_to_children(devices):
    """Includes md raid devices among children of their parent devices.
    
    Assumption: specific order of rows in lsblk output.
    """
     
    rev_devices = reversed(devices)
    
    for device in rev_devices:  
                          
        if device['type'].startswith('raid'):
            parent = next(rev_devices)
            utils.connect(parent, device)
            

def merge_raid_devices(devices):
    """Merges multiple rows (from lsblk output) for one md raid device. 
    Preserves all information (all parent devices).
    """
    
    raids = [device for device in devices if device['type'].startswith('raid')]
    copy_raids = list(raids)
    result = []
    checked = []
    
    for raid in raids:
        
        if raid['uuid'] not in checked:
            for raid2 in copy_raids:
                
                if raid['uuid'] == raid2['uuid']:
                    for parent_uuid in raid2['parents']:
                        
                        parent = utils.get_by_uuid(parent_uuid, devices)
                        if parent:
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
    
    for device in devices:
        
        if device['uuid'] not in unique:                
            unique.append(device['uuid'])
            result.append(device)
            
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
    
    copy_elements = list(elements)
    encryptions = []
    
    for elem in elements:
        
        if elem['encrypted'] and elem['children']:
            crypt = utils.get_by_uuid(elem['children'][0],copy_elements)
            
            if crypt:
                elem['mountpoint'] = crypt['mountpoint']
                elem['fstype'] = crypt['fstype']
                elem['children'] = crypt['children']
                
                encryptions.append(crypt['uuid'])
                
                for child_uuid in elem['children']:
                    
                    child = utils.get_by_uuid(child_uuid, elements)
                    
                    if child:    
                        child['parents'].remove(crypt['uuid'])
                        child['parents'].append(elem['uuid'])
                
        elif elem['encrypted']:
            elem['fstype'] = ''
            
    return [elem for elem in elements if elem['uuid'] not in encryptions]

