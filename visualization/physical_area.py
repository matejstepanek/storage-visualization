'''
Created: 2015

@author: mstepane@redhat.com

Area with everything that could be a physical volume:
disks, partitions, md raids.
'''

from gi.repository import Gtk   #@UnresolvedImport

from data.utils import get_by_uuid


class PhysicalArea(Gtk.Box):
    """Area with disks, partitions and md raids.
    
    Disks are alphabetically ordered. 
    """
    
    def __init__(self, scheme, main_window):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        
        
        disks_partitions_box = Gtk.Box(spacing=scheme.H_GAP_BIG)
        self.pack_start(disks_partitions_box, False, False, 0)
        
        self.md_raid_present = False
        self.md_raids_added = []
        
        self.ordered_pvs = []
        
        for disk in main_window.disks_loops:
            
            disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                               spacing=scheme.V_GAP_SMALL)
            disks_partitions_box.add(disk_box)
            
            scheme.add_rectangle(disk, disk_box)
            
            part_row = Gtk.Box(spacing=scheme.H_GAP_SMALL)
            disk_box.add(part_row)
            
            for element_uuid in disk['children']:
                
                element = get_by_uuid(element_uuid, main_window.all_elements)
                
                if element:
                    if element['type'] == 'pv':
                        self.ordered_pvs.append(element)
                        break
                    elif element['type'] == 'part':
                        scheme.add_rectangle(element, part_row)
                    else:
                        self.add_raid(element, scheme)
    
                    
                    for element2_uuid in element['children']:
                        
                        element2 = get_by_uuid(element2_uuid, main_window.all_elements)
                        
                        if element2:
                            if element2['type'] == 'pv':
                                self.ordered_pvs.append(element2)
                                break
                            
                            self.add_raid(element2, scheme)

    
    def add_raid(self, element, scheme):
        """Adds a separate md raid layer and a separator.
        """
        
        if not self.md_raid_present:
            
            separator = Gtk.Separator(margin_top=scheme.V_GAP_BIG,
                                       margin_bottom=scheme.V_GAP_BIG)
            self.pack_start(separator, False, False, 0)
            
            self.mdraids_row = Gtk.Box(spacing=scheme.H_GAP_BIG)
            self.pack_start(self.mdraids_row, False, False, 0)
            
            self.md_raid_present = True
            
            
        if element['uuid'] not in self.md_raids_added:
                        
            scheme.add_rectangle(element, self.mdraids_row)
            
            self.md_raids_added.append(element['uuid'])
        
             
