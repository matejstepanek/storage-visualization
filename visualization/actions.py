'''
Created: 2015

@author: mstepane@redhat.com

Actions to perform when various signals are emitted or menu items activated.
'''


def destroy_children(widget):
        """Destroys all children of a given widget.
        """
        
        children = widget.get_children()
        
        for child in children:
            
            child.destroy()
            

def clear_dependencies(main_window):
        """Unhiglights all rectangles.
        """
        
        rectangles = main_window.scheme_box.rectangles
        
        for rec in rectangles.itervalues():
            
            rec.set_name('Rectangle')


def create_pv(menu_item, element):
        
    print 'Creating pv', element['label']['name']


def create_vg(menu_item, pv):
    
    print 'Creating new volume group on physical volume', pv['label']['name']
    
    
def create_lv(menu_item, vg):
    
    print 'Creating logical volume in volume group', vg['name']
    

def create_thin_lv(menu_item, pool):
    
    print 'Creating thin logical volume in thin pool', pool['name']
    

def create_snapshot(menu_item, element):
    
    print 'Creating snapshot of logical volume', element['label']['name']
    

def vg_extend(menu_item, vg):
    
    print 'Extending volume group %s with physical volume' %vg['name']
    

def vg_reduce(menu_item, vg):
    
    print 'Removing physical volume from volume group', vg['name']


def remove_pv_from_vg(menu_item, pv):
    
    print 'Removing pv %s from vg %s' %(pv['label']['name'], pv['vg_name'])


def add_pv_to_vg(menu_item, element):
    
    print 'Adding pv %s to volume group' %element['label']['name']


def remove_element(menu_item, element):
    
    print 'Removing element', element['label']['name']
        

def format_element(menu_item, element):
    
    print 'Formating', element['label']['name']
    

def mount_file_system(menu_item, element):
    
    print 'Mounting fs on', element['label']['name']
    

def unmount_file_system(menu_item, element):
    
    print 'Unmounting fs on', element['label']['name']
    

def remove_encryption(menu_item, element):
    
    print 'Removing encryption from', element['label']['name']
    

def encrypt(menu_item, element):
    
    print 'Encrypting', element['label']['name']
    
