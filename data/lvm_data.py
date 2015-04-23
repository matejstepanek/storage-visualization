'''
Created: 2015

@author: mstepane@redhat.com

Collecting data from pvs, vgs and lvs commands outputs.
'''

import subprocess
from itertools import groupby

import utils


def get_pvs():
    """Returns list of physical volumes in system.
    
    Each item in the list is a dictionary with these keys: 
    uuid, name, type, mountpoint, fstype, size, parents, children,
    encrypted, label, vg_name.
    """
    
    pvs_output = subprocess.check_output(['sudo', 'pvs', '--units', 'b', 
                                   '--noheadings', '--separator', '@', '-o', 
                                   'pv_uuid,pv_name,dev_size,vg_name'])

    pvs_list = pvs_output.split('\n')[:-1]

    keys = ['uuid', 'name', 'size', 'vg_name']
    pvs = [dict(zip(keys, pv.split('@'))) for pv in pvs_list]
    
    for pv in pvs:
        
        process_lvm_element(pv)
        
        pv['type'] = 'pv'
        pv['uuid'] = pv['uuid'] + '@pv'
        pv['occupied'] = -1
        
        utils.set_label(pv)
    
    return pvs


def process_lvm_element(elem):
    """Sets and modifies attributes of lvm element.
    """
    
    elem['uuid'] = ''.join([elem['name'], '@', elem['uuid'].strip()])
    elem['mountpoint'] = ''
    elem['fstype'] = ''
    elem['size'] = int(elem['size'][:-1])  # Removes 'B' from the end of a size
    elem['parents'] = []
    elem['children'] = []
    elem['encrypted'] = False


def get_vgs():
    """Returns list of volume groups in system.
    
    Each item in the list is a dictionary with these keys:
    uuid, name, type, mountpoint, fstype, size, occupied, parents, children, 
    encrypted, label.
    """
    
    vgs_output = subprocess.check_output(['sudo', 'vgs', '--units', 'b',
                                   '--noheadings', '--separator', '@', '-o', 
            'vg_uuid,vg_name,vg_size,vg_free'])
    
    vgs_list = vgs_output.split('\n')[:-1]
    
    keys = ['uuid','name','size','vg_free']    
    vgs = [dict(zip(keys, vg.split('@'))) for vg in vgs_list]
    
    for vg in vgs:
        
        process_lvm_element(vg)
        
        vg['type'] = 'vg'
        vg['occupied'] = vg_calculate_occupied_space(vg)
        
        utils.set_label(vg) 
    
    return vgs


def vg_calculate_occupied_space(vg):
    """Returns percentage of occupied space.
    
    Also removes key vg_free.
    """
    
    free = float(vg['vg_free'][:-1])
    
    vg['occupied'] = round(((1 - free / vg['size']) * 100), 1)
    
    vg.pop('vg_free')
    
    return vg['occupied']


def get_lvs(lsblk_lvm, pvs):
    """Returns lists of logical volumes in system - standard and internal.
    
    Each item in the list is a dictionary with these keys:   
    uuid, name, type, mountpoint, fstype, size, occupied, parents, children, 
    encrypted, label, vg_name, origin (for snapshots), segtype, pool_lv,
    is_origin.
    """
    
    lvs_output = subprocess.check_output(['sudo', 'lvs', '-a', '--units', 'b', 
                                   '--noheadings', '--separator', '@', '-o',
        'lv_uuid,lv_name,vg_name,origin,lv_size,segtype,pool_lv,data_percent'])  
    
    lvs = lvs_output.split('\n')[:-1]
    
    keys = ['uuid','name','vg_name','origin','size','segtype','pool_lv','occupied']        
    lvs = [dict(zip(keys, lv.split('@'))) for lv in lvs]
        
    for lv in lvs:
        
        process_lvm_element(lv)
        
        lv['type'] = 'lv'
        lv['is_origin'] = False
        lv['occupied'] = lv_calculate_occupied_space(lv)
        
        lsblk_equivalent = get_lv_from_lsblk(lv, lsblk_lvm)
        if lsblk_equivalent:
            add_lsblk_info(lv, lsblk_equivalent, pvs)
                
    standard_not_unique = [l for l in lvs if not l['name'].startswith('[')]
    standard = [key for key,_group in groupby(sorted(standard_not_unique))]
    internal = [lv for lv in lvs if lv['name'].startswith('[')]

    tag_origins(standard)
    
    for lv in lvs:
        
        if lv['segtype'] == 'cache':
            add_cache_pool_to_standard(lv, internal, standard)
        
        utils.set_label(lv, internal)
    
    return (standard, internal)
    

def lv_calculate_occupied_space(lv):
    """Returns percentage of occupied space.
    """
    
    if lv['occupied']:
        lv['occupied'] = round(float(lv['occupied'].replace(',', '.')), 1)
    else:
        lv['occupied'] = -1
    
    return lv['occupied']
    

def get_lv_from_lsblk(lv, lsblk_lvm):
    """Given logical volume returns corresponding device from lsblk output.
    
    LVM device in lsblk output has this form: vg_name-lv_name
    where every dash in vg_name or lv_name is doubled.  
    """
    
    vg_name = lv['vg_name'].replace('-','--')
    lv_name = lv['name'].replace('-','--')
    
    key = ''.join([vg_name, '-', lv_name])
    
    result = None
    
    for elem in lsblk_lvm:
        
        if elem['name'] == key:
            result = elem
            break
    
    return result


def add_lsblk_info(lv, lsblk_equivalent, pvs):
    """Enrich logical volume attributes with information from lsblk output. 
    """
    
    lv['mountpoint'] = lsblk_equivalent['mountpoint']
    lv['fstype'] = lsblk_equivalent['fstype']
    lv['children'] = lsblk_equivalent['children']
    lv['encrypted'] = lsblk_equivalent['encrypted']
    
    if lv['occupied'] == -1:
        lv['occupied'] = lsblk_equivalent['occupied']
      
    for pv_uuid in lsblk_equivalent['children']:
        
        pv = utils.get_by_uuid(pv_uuid, pvs)
        if pv:
            pv['parents'] = [lv['uuid']]


def tag_origins(lvs):
    """Recognizes origins of snapshots. Tags them. (key 'is_origin')
    """
    
    tagged_origins = []
    
    for lv in lvs:
        
        if lv['origin'] and lv['segtype'] != 'cache':
            origin = utils.get_by_name(lv['origin'], lvs)
            
            if origin and origin not in tagged_origins:
                origin['is_origin'] = True
                tagged_origins.append(origin)


def add_cache_pool_to_standard(lv, internal, standard):
    """We don't display internal logical volumes. [in brackets]
    Cache pool is internal logical volume, but we want to display it.
    So we add it to the list of standard logical volumes.
    """
    
    cache_pool = utils.get_by_name(lv['pool_lv'], internal)
    if cache_pool:
        standard.append(cache_pool)

