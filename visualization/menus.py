'''
Created: 2015

@author: mstepane@redhat.com

Actions to perform when various signals are emitted.
'''

from gi.repository import Gtk   #@UnresolvedImport

from data.utils import get_by_name, FS_TYPES
import actions


def get_menu(element, main_window):
    """Returns context menu for a given element.
    """
    
    typ = element['type']
    
    menu = None
    
    if typ in ['disk', 'loop']:
        menu = MenuDisk(element, main_window)
            
    elif typ == 'part' or typ.startswith('raid'):
        menu = MenuPartRaid(element, main_window)
          
    elif typ == 'pv':
        menu = MenuPV(element, main_window)
          
    elif typ == 'vg':
        menu = MenuVG(element, main_window)
          
    elif typ == 'lv':
        if element['segtype'] == 'thin-pool':
            menu = MenuPool(element, main_window)
        else:
            menu = MenuLV(element, main_window)
    
    return menu


def get_item_format(element):
    
    item = Gtk.MenuItem('Format')
    item.connect('activate', actions.format_element, element)
    
    if element['children']:
        item.set_sensitive(False)
    
    return item
    
    
def get_item_create_pv(element):
    
    item = Gtk.MenuItem('Create physical volume')
    item.connect('activate', actions.create_pv, element)
    
    if element['children'] or element['fstype']:
        item.set_sensitive(False)

    return item


def get_item_mounting(element):
    
    if element['mountpoint']:
        item = Gtk.MenuItem('Unmount file system')
        item.connect('activate', actions.unmount_file_system, element)
    else:
        item = Gtk.MenuItem('Mount file system')
        item.connect('activate', actions.mount_file_system, element)
    
    return item


def get_item_encryption(element):
    
    if element['encrypted']:
        item = Gtk.MenuItem('Remove encryption')
        item.connect('activate', actions.remove_encryption, element)
    else:
        item = Gtk.MenuItem('Encrypt')
        item.connect('activate', actions.encrypt, element)
    
    if element['children'] or element['fstype']:
        item.set_sensitive(False)

    return item


def get_item_remove(element):
    
    item = Gtk.MenuItem('Remove')
    item.connect('activate', actions.remove_element, element)
    
    if element['children']:
        item.set_sensitive(False)
        
    return item
    

class MenuDisk(Gtk.Menu):
    
    def __init__(self, disk, main_window):
        
        Gtk.Menu.__init__(self)
        
        
        item = get_item_create_pv(disk)
        self.add(item)
        
        item = get_item_format(disk)
        self.add(item)
        
        if disk['fstype'] in FS_TYPES:
            item = get_item_mounting(disk)
            self.add(item)
        
        item = get_item_encryption(disk)
        self.add(item)
        
        
        self.show_all()
        
        
class MenuPartRaid(Gtk.Menu):
    
    def __init__(self, element, main_window):
        
        Gtk.Menu.__init__(self)
        
        
        item = get_item_create_pv(element)
        self.add(item)
        
        item = get_item_format(element)
        self.add(item)
        
        if element['fstype'] in FS_TYPES:
            item = get_item_mounting(element)
            self.add(item)
        
        item = get_item_encryption(element)
        self.add(item)
        
        item = get_item_remove(element)
        self.add(item)
        
        
        self.show_all()        
        
        
class MenuPV(Gtk.Menu):
    
    def __init__(self, pv, main_window):
        
        Gtk.Menu.__init__(self)
        
        
        if pv['vg_name']:
            
            vg = get_by_name(pv['vg_name'], main_window.all_elements)
            
            item = Gtk.MenuItem('Remove from volume group ' + pv['vg_name'])
            item.connect('activate', actions.remove_pv_from_vg, pv)
            
            if len(vg['parents']) <= 1:
                item.set_sensitive(False)
            
            self.add(item)
        
        else:
            item = Gtk.MenuItem('Create volume group here')
            item.connect('activate', actions.create_vg, pv)
            self.add(item)
            
            item = Gtk.MenuItem('Add to volume group')
            item.connect('activate', actions.add_pv_to_vg, pv)
            self.add(item)
   
        item = get_item_remove(pv)
        self.add(item)
        
        
        self.show_all() 
        
        
class MenuVG(Gtk.Menu):
    
    def __init__(self, vg, main_window):
        
        Gtk.Menu.__init__(self)
        
        
        item = Gtk.MenuItem('Create logical volume')
        item.connect('activate', actions.create_lv, vg)
        if vg['occupied'] == 100:
            item.set_sensitive(False)
        self.add(item)
        
        item = Gtk.MenuItem('Add physical volume')
        item.connect('activate', actions.vg_extend, vg)
        self.add(item)
        
        item = Gtk.MenuItem('Remove physical volume')
        item.connect('activate', actions.vg_reduce, vg)
        if len(vg['parents']) <= 1:
                item.set_sensitive(False)
        self.add(item)
        
        item = Gtk.MenuItem('Remove')
        item.connect('activate', actions.remove_element, vg)
        if vg['children']:
            item.set_sensitive(False)
        self.add(item)
        
        
        self.show_all() 


class MenuLV(Gtk.Menu):
    
    def __init__(self, lv, main_window):
        
        Gtk.Menu.__init__(self)
        
        
        item = get_item_format(lv)
        self.add(item)
        
        item = Gtk.MenuItem('Create snapshot')
        item.connect('activate', actions.create_snapshot, lv)
        self.add(item)
        
        if lv['fstype'] in FS_TYPES:
            item = get_item_mounting(lv)
            self.add(item)
        
        item = get_item_encryption(lv)
        self.add(item)
        
        item = get_item_remove(lv)
        self.add(item)
        
        
        self.show_all() 
        

class MenuPool(Gtk.Menu):
    
    def __init__(self, pool, main_window):
        
        Gtk.Menu.__init__(self)
        
        
        item = Gtk.MenuItem('Create thin logical volume')
        item.connect('activate', actions.create_thin_lv, pool)
        if pool['occupied'] == 100:
            item.set_sensitive(False)
        self.add(item)
        
        item = get_item_remove(pool)
        self.add(item)
        
        
        self.show_all()

