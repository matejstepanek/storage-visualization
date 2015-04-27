'''
Created: 2015

@author: mstepane@redhat.com

Collecting information about storage elements in the system.

Instructions when running in eclipse:
Add this line to the end of /etc/sudoers ('username' replace with your username)
username ALL = NOPASSWD: ALL 
And comment this line (if it's present) in /etc/sudoers
Defaults    requiretty
It enables you to run sudo commands without entering the password. 
'''

import lsblk_data
import lvm_data
import utils


class Elements:
    """Collecting information about storage elements in the system.
    
    Putting together data from lsblk, lvs, vgs and pvs commands.
    """
           
    def __init__(self):
        
        self.pvs = lvm_data.get_pvs()
        self.vgs = lvm_data.get_vgs()  
        
        lsblk_with_pvs = lsblk_data.get_lsblk_elements(self.pvs)
        
        lsblk_no_lvs, lsblk_lvs = self.separate_lvs(lsblk_with_pvs)
        
        self.lvs, _internal_lvs = lvm_data.get_lvs(lsblk_lvs, self.pvs)
        
        self.set_dependencies_lvm(self.pvs, self.vgs, self.lvs)
        
        self.all_elements = lsblk_no_lvs + self.vgs + self.lvs
        self.disks_loops = [d for d in lsblk_no_lvs if d['type'] in ['disk', 'loop']]


    def separate_lvs(self, lsblk):
        """Divides lsblk elements into 2 lists: 
            1) disk, loops, partitions, md raids, pvs
            2) lvm devices (= logical volumes)
        """
        
        lsblk_lvm = []
        copy_lsblk = lsblk[:]
        
        for elem in copy_lsblk:
            
            if elem['type'] == 'lvm':                      
                lsblk.remove(elem)
                
                if elem not in lsblk_lvm:
                    lsblk_lvm.append(elem)
                    
        return (lsblk, lsblk_lvm)


    def set_dependencies_lvm(self, pvs, vgs, lvs):
        """Sets dependencies between volume groups and physical/logical volumes.
        
        Elements are connected by keys parents and children. 
        """
     
        for pv in pvs:
            self.connect_pv_vg(pv, vgs)
                        
        for lv in lvs:                
            
            if lv['pool_lv'] and lv['segtype'] != 'cache':
                self.connect_thinlv_pool(lv, lvs)
            else:
                self.connect_lv_vg(lv, vgs)
                
    
    def connect_pv_vg(self, pv, vgs):
        """Connects physical volume to its volume group.
        """
        
        for vg in vgs:
            
            if vg['name'] == pv['vg_name']:
                utils.connect(pv, vg)
                break
    
    
    def connect_thinlv_pool(self, thinlv, lvs):
        """Connects thin logical volume to its pool.
        """
        
        for lv in lvs:
            
            if thinlv['pool_lv'] == lv['name']:
                utils.connect(lv, thinlv)
                break
    
    
    def connect_lv_vg(self, lv, vgs):
        """Connects logical volume to its volume group.
        """
        
        for vg in vgs:
            
            if lv['vg_name'] == vg['name']:
                utils.connect(vg, lv)
                break


#################################### TESTING ###################################

if __name__ == '__main__':
    data = Elements()
    print '-------------------------------------------------'
    for x in data.all_elements:
        print x['name'], x

        