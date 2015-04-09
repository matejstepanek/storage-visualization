'''
Created: 2015

@author: mstepane@redhat.com

Collecting data from pvs, vgs and lvs commands outputs.
'''

import utils
import subprocess
from itertools import groupby


class LvmData:
    """Collecting data from pvs, vgs and lvs commands outputs.
    """

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
            utils.set_label(pv) 
                       
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
        elem['fsoccupied'] = -1

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
            utils.set_label(vg) 
        
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
                lv['fsoccupied'] = dev['fsoccupied']
                
                for ch_uuid in dev['children']:
                    ch = utils.get_by_uuid(ch_uuid, pvs)
                    ch['parents'] = [lv['uuid']]
                    
        standard_not_unique = [l for l in lvs if not l['name'].startswith('[')]
        standard = [key for key,_group in groupby(sorted(standard_not_unique))]
        internal = [lv for lv in lvs if lv['name'].startswith('[')]
    
        for lv in lvs:
            if lv['origin']:
                if lv['segtype'] != 'cache':
                    
                    # Sets atributte 'is_origin' (origin of a snapshot)
                    origin = utils.get_by_name(lv['origin'], standard)
                    if origin:
                        origin['is_origin'] = True
            
            if lv['segtype'] == 'cache':
                cache_pool = utils.get_by_name(lv['pool_lv'], internal)
                standard.append(cache_pool)
            
            utils.set_label(lv, internal)
        
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
                    utils.connect(pv, vg)
                    break
                        
        for lv in lvs:                
            if lv['pool_lv'] and lv['segtype'] != 'cache':
                # Connect thin lv to its pool
                for lv2 in lvs:
                    if lv['pool_lv'] == lv2['name']:
                        parent = lv2
                        break
                utils.connect(parent, lv)
            else:
                # Connect lv to vg
                for vg in vgs:
                    if lv['vg_name'] == vg['name']:
                        utils.connect(vg, lv)
                        break
                    
