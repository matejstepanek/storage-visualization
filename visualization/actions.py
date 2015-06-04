'''
Created: 2015

@author: mstepane@redhat.com

Actions to perform when various signals are emitted or menu items activated.
'''

import subprocess

import dialogs


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


def create_pv(menu_item, element, main_window):
        
    dialog = dialogs.DialogCreatePv(element, main_window)
    response = dialog.run()

    if response == 1:
        
        output = subprocess.check_output(['sudo', 'pvcreate',
                                          '/dev/%s' %element['name']])
        print output
        
        main_window.__init__()

    dialog.destroy()


def create_vg(menu_item, pv):
    
    print 'Should happen, but not implemented:\
    Creating new volume group on physical volume', pv['label']['name']
    
    
def create_lv(menu_item, vg):
    
    print 'Should happen, but not implemented:\
    Creating logical volume in volume group', vg['name']
    

def create_thin_lv(menu_item, pool):
    
    print 'Should happen, but not implemented:\
    Creating thin logical volume in thin pool', pool['name']
    

def create_snapshot(menu_item, element):
    
    print 'Should happen, but not implemented:\
    Creating snapshot of logical volume', element['label']['name']
    

def vg_extend(menu_item, vg, main_window):
    
    dialog = dialogs.DialogVgExtend(vg, main_window)
    response = dialog.run()

    if response == 1:
        
        pv_name = dialog.combo.get_active_text()
        
        output = subprocess.check_output(['sudo', 'vgextend', vg['name'],
                                          '/dev/'+pv_name])
        print output
        
        main_window.__init__()

    dialog.destroy()
    

def vg_reduce(menu_item, vg, main_window):
    
    dialog = dialogs.DialogVgReduce(vg, main_window)
    response = dialog.run()

    if response == 1:
        
        pv_name = dialog.combo.get_active_text()
        
        output = subprocess.check_output(['sudo', 'vgreduce', vg['name'],
                                          '/dev/'+pv_name])
        print output
        
        main_window.__init__()

    dialog.destroy()


def remove_pv_from_vg(menu_item, pv, main_window):
    
    dialog = dialogs.DialogRemovePvFromVg(pv, main_window)
    response = dialog.run()

    if response == 1:
        
        output = subprocess.check_output(['sudo', 'vgreduce', pv['vg_name'],
                                          pv['name']])
        print output
        
        main_window.__init__()

    dialog.destroy()


def add_pv_to_vg(menu_item, pv, main_window):
    
    dialog = dialogs.DialogAddToVg(pv, main_window)
    response = dialog.run()

    if response == 1:
        
        vg_name = dialog.combo.get_active_text()
        
        output = subprocess.check_output(['sudo', 'vgextend', vg_name,
                                          pv['name']])
        print output
        
        main_window.__init__()

    dialog.destroy()
    

def remove_element(menu_item, element, main_window):
    
    if element['type'] != 'pv':
        
        print 'Should happen, but not implemented:\
        Removing element', element['label']['name']
        
    else:
        dialog = dialogs.DialogRemoveElement(element, main_window)
        response = dialog.run()
        
        if response == 1:
            
            output = subprocess.check_output(['sudo', 'pvremove', element['name']])
            print output
            
            main_window.__init__()
        
        dialog.destroy()
        

def format_element(menu_item, element):
    
    print 'Should happen, but not implemented:\
    Formating', element['label']['name']
    

def mount_file_system(menu_item, element):
    
    print 'Should happen, but not implemented:\
    Mounting fs on', element['label']['name']
    

def unmount_file_system(menu_item, element):
    
    print 'Should happen, but not implemented:\
    Unmounting fs on', element['label']['name']
    

def remove_encryption(menu_item, element):
    
    print 'Should happen, but not implemented:\
    Removing encryption from', element['label']['name']
    

def encrypt(menu_item, element):
    
    print 'Should happen, but not implemented:\
    Encrypting', element['label']['name']
    
