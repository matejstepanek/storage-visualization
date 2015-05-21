'''
Created: 2015

@author: mstepane@redhat.com

Auxiliary functions.
'''


FS_TYPES = ['ext3', 'ext4', 'vfat', 'ntfs', 'btrfs', 'xfs']


def get_by_uuid(uuid, elements):
    """From the list of storage elements returns an element with a given uuid.
    """
    
    match = None
    
    for element in elements:
        
        if element['uuid'] == uuid:
            match = element
            break
    
    return match


def get_by_name(name, elements):
    """From the list of storage elements returns an element with a given name.
    """
    
    match = None
    
    for element in elements:
        
        if element['name'] == name:
            match = element
            break
        
    return match


def connect(parent, child):
    """Connects parent element with child element.
    """
    
    if child['uuid'] not in parent['children']:
        parent['children'].append(child['uuid'])
        
    if parent['uuid'] not in child['parents']:
        child['parents'].append(parent['uuid'])


def set_label(element, internal_lvs = None):
    """Sets a label of a storage element.
    
    The label contains information about element's:
        1) name
        2) content - file system and mountpoint
        3) size - includes available space size and percentage of occupied space
        4) type
    """

    element['label'] = {}
    
    element['label']['name'] = element['name'].split('/')[-1]
    
    if element['fstype']:
        element['label']['content'] = element['fstype']
        
        if element['mountpoint']:
            element['label']['content'] += ' - mounted in %s' %element['mountpoint']
    else:
        element['label']['content'] = '  -  '
    
    set_label_size(element)
    
    set_label_type(element, internal_lvs)


def set_label_size(element):
    
    element['label']['size'] = make_readable(element['size'])
    
    if element['occupied'] >= 0:

        free = element['size'] * (1 - element['occupied']/100)
        
        element['label']['size'] += ' - %s available (%.1f %% occupied)' %(
                                    make_readable(free), element['occupied'])


def make_readable(size):
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


def set_label_type(element, internal_lvs):
    
    element['label']['type'] = {}
    
    typ = element['type']
    
    if typ == 'disk':
        element['label']['type']['short'] = 'Disk'
        element['label']['type']['long']  = 'Disk'
                        
    elif typ == 'loop':
        element['label']['type']['short'] = 'Loop device'
        element['label']['type']['long']  = 'Loop device'    
    
    elif typ == 'part':
        element['label']['type']['short'] = 'Partition'
        element['label']['type']['long']  = 'Partition'
    
    elif typ.startswith('raid'):
        element['label']['type']['short'] = typ.capitalize()
        element['label']['type']['long']  = typ.capitalize()
    
    elif typ == 'pv':
        element['label']['type']['short'] = 'PV'
        element['label']['type']['long']  = 'Physical volume'
    
    elif typ == 'vg':
        element['label']['type']['short'] = 'VG'
        element['label']['type']['long']  = 'Volume group'
    
    elif typ == 'lv':
        set_label_type_lv(element, internal_lvs)
        
    else:
        element['label']['type']['short'] = typ.capitalize()
        element['label']['type']['long'] = typ.capitalize()
        
    if element['encrypted']:
        element['label']['type']['long'] += ', encrypted'


def set_label_type_lv(element, internal_lvs):
    """Sets label type of the logical volume.
    """
    
    type_lv = element['segtype']
         
    if type_lv == 'cache':
        element['label']['type']['short'] = 'LV with cache'
        element['label']['type']['long']  = 'Logical volume with cache'
    
    elif type_lv == 'thin-pool':
        element['label']['type']['short'] = 'Thin pool'
        element['label']['type']['long']  = 'Pool for thin logical volumes'
        
        is_raid = check_tdata(element, internal_lvs)
        if is_raid:
            element['label']['type']['short'] += ', ' + is_raid
            element['label']['type']['long'] += ', ' + is_raid
             
    elif type_lv == 'thin':
         
        if element['origin']:
            element['label']['type']['short'] = 'Thin snap.'
            element['label']['type']['long']  = 'Thin snapshot of %s' %(
                                                            element['origin'])
        else:    
            element['label']['type']['short'] = 'Thin LV'
            element['label']['type']['long']  = 'Thin logical volume'
             
    elif element['origin']:
        element['label']['type']['short'] = 'Snapshot'
        element['label']['type']['long']  = 'Snapshot of %s' %element['origin']
    
    else:
        element['label']['type']['short'] = 'LV'
        element['label']['type']['long']  = 'Logical volume'
     
    if type_lv.startswith('raid'):
            element['label']['type']['short'] += ', ' + type_lv
            element['label']['type']['long'] += ', ' + type_lv 


def check_tdata(thin_pool, internal_lvs):
    """Checks if thin pool is lvm raid as well.
    
    Returns type of raid or None.
    """
    
    result = None
    key = '[%s_tdata]' %thin_pool['name']
    
    for lv in internal_lvs:
        if lv['name'] == key:
            if lv['segtype'].startswith('raid'):
                result = lv['segtype']
                break
    
    return result

