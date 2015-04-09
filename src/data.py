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


class Data:
    """Collecting information about storage elements in the system.
    
    Putting together data from lsblk, lvs, vgs and pvs commands.
    """
           
    def get_data(self):
        """Returns storage elements connected into tree structure.
        """
        
        lvmdata = lvm_data.LvmData()
        pvs = lvmdata.get_pvs()
        vgs = lvmdata.get_vgs()  
        
        lsblkdata = lsblk_data.LsblkData()
        lsblk_with_pvs = lsblkdata.get_lsblk_elements(pvs)
        
        (lsblk_no_lvm, lsblk_lvm) = self.separate_lvm_elements(lsblk_with_pvs)
        
        (lvs, _internal_lvs) = lvmdata.get_lvs(lsblk_lvm, pvs)
        
        lvmdata.set_dependencies_lvm(pvs, vgs, lvs)
        
        all_elems = lsblk_no_lvm + vgs + lvs
        disks_loops = [d for d in lsblk_no_lvm if d['type'] in ['disk', 'loop']]
        
        return (all_elems, pvs, vgs, lvs, disks_loops)
      
    def separate_lvm_elements(self, lsblk):
        """Divides devices into 2 lists: 
            1) disk, loops, partitions, md raids
            2) lvm devices (i.e. logical volumes) 
        """
        
        lsblk_lvm = []
        copy_lsblk = lsblk[:]
        
        for dev in copy_lsblk:
            
            if dev['type'] == 'lvm':                      
                lsblk.remove(dev)
                
                if dev not in lsblk_lvm:
                    lsblk_lvm.append(dev)
                    
        return (lsblk, lsblk_lvm)

                
#################################### TESTING ###################################

if __name__ == '__main__': 
    data = Data()
    (all_elems, pvs, vgs, lvs, disks_loops) = data.get_data()
    print '-------------------------------------------------'
    for x in all_elems:
        print x['name'], x
        

        