'''
Created: 2015

@author: mstepane@redhat.com

Auxiliary functions.
'''


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
    """From the list of storage elements returns an element with a given name.
    """
    
    match = None
    
    for elem in elements:
        
        if elem['name'] == name:
            match = elem
            break
        
    return match


def connect(parent, child):
    """Connects parent element with child element.
    """
    
    if child['uuid'] not in parent['children']:
        parent['children'].append(child['uuid'])
        
    if parent['uuid'] not in child['parents']:
        child['parents'].append(parent['uuid'])


def set_label(elem, internal_lvs = None):
    """Sets a label of a storage element.
    
    The label contains information about element's:
        1) name
        2) content - file system and mountpoint
        3) size - includes available space size and percentage of occupied space
        4) type
    """

    elem['label'] = {}
    
    elem['label']['name'] = elem['name'].split('/')[-1]
    
    elem['label']['content'] = elem['fstype']
    if elem['mountpoint']:
        elem['label']['content'] += ' - mounted in %s' %elem['mountpoint']
    
    set_label_size(elem)
    
    set_label_type(elem, internal_lvs)


def set_label_size(elem):
    
    elem['label']['size'] = make_readable(elem['size'])
    
    if elem['occupied'] >= 0:
#         print elem['name'], elem['occupied']
        free = elem['size'] * (1 - elem['occupied']/100)
        
        elem['label']['size'] += ' - %s available (%.1f %% occupied)' %(
                                        make_readable(free), elem['occupied'])


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


def set_label_type(elem, internal_lvs):
    
    elem['label']['type'] = {}
    
    typ = elem['type']
    
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
        set_label_type_lv(elem, internal_lvs)
        
    else:
        elem['label']['type']['short'] = typ.capitalize()
        elem['label']['type']['long'] = typ.capitalize()
        
    if elem['encrypted']:
        elem['label']['type']['long'] += ', encrypted'


def set_label_type_lv(elem, internal_lvs):
    """Sets label type of the logical volume.
    """
    
    type_lv = elem['segtype']
         
    if type_lv == 'cache':
        elem['label']['type']['short'] = 'LV with cache'
        elem['label']['type']['long']  = 'Logical volume with cache %s' %(
                                                            elem['pool_lv'])
    elif type_lv == 'cache-pool':
        elem['label']['type']['short'] = 'Cache'
        elem['label']['type']['long']  = 'Cache'
    
    elif type_lv == 'thin-pool':
        elem['label']['type']['short'] = 'Thin pool'
        elem['label']['type']['long']  = 'Pool for thin logical volumes'
        
        is_raid = check_tdata(elem, internal_lvs)
        if is_raid:
            elem['label']['type']['short'] += ', ' + is_raid
            elem['label']['type']['long'] += ', ' + is_raid
             
    elif type_lv == 'thin':
         
        if elem['origin']:
            elem['label']['type']['short'] = 'Thin snap.'
            elem['label']['type']['long']  = 'Thin snapshot of %s' %(
                                                            elem['origin'])
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

