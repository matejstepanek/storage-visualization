'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage elements in dependency trees.
'''

from gi.repository import Gtk, GdkPixbuf   #@UnresolvedImport

from data.utils import get_by_uuid

FS_TYPES = ['ext3', 'ext4', 'vfat', 'ntfs', 'btrfs', 'xfs']


class TreePanel(Gtk.Box): 
    """Panel with tree structure of storage elements.
    """      
    
    def __init__(self, window, all_elems, vgs, lvs, disks_loops):
        
        self.window = window
        self.all_elems = all_elems
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                          width_request=200)                                      
        # Disk tree        
        store_disks = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_disks, all_elems, disks_loops, 'name')
        view_disks = TreeView(store_disks, all_elems, self.window)
        view_disks.set_headers_visible(False)
#         view_disks.expand_all()
        view_disks.set_enable_tree_lines(True)
        
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        view_disks.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Disks', renderer_text, text=1)
        view_disks.append_column(column_text)
              
        scrolled_window_view_disks = Gtk.ScrolledWindow()
        scrolled_window_view_disks.add(view_disks)
        
        # VG tree
        store_vgs = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_vgs, all_elems, vgs, 'name')
        view_vgs = TreeView(store_vgs, all_elems, self.window)
        view_vgs.set_headers_visible(False)
#         view_vgs.expand_all()
        view_vgs.set_enable_tree_lines(True)
                
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        view_vgs.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Volume groups', renderer_text, text=1)        
        view_vgs.append_column(column_text)
        
        scrolled_window_view_vgs = Gtk.ScrolledWindow()
        scrolled_window_view_vgs.add(view_vgs)
        
        # mountpoints tree
        mpoints = []
        for elem in all_elems:
            if elem['mountpoint']:
                mpoints.append(elem)
        
        store_mountpoints = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_mountpoints, all_elems, mpoints, 'mountpoint')
        view_mountpoints = TreeView(store_mountpoints, all_elems, self.window)
        view_mountpoints.set_headers_visible(False)
#         view_mountpoints.expand_all()
        view_mountpoints.set_enable_tree_lines(True)
                
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        view_mountpoints.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Mount points', renderer_text, text=1)        
        view_mountpoints.append_column(column_text)
        
        scrolled_window_view_mountpoints = Gtk.ScrolledWindow()
        scrolled_window_view_mountpoints.add(view_mountpoints)
        
        # Sets the stack and his switcher.
        stack = Gtk.Stack()
        
        stack.add_titled(scrolled_window_view_disks, 'disks', 'Disks')        
        stack.add_titled(scrolled_window_view_vgs, 'vgs', 'Volume groups')
        stack.add_titled(scrolled_window_view_mountpoints, 'mountpoints', 'Mount points')

        
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        
        self.pack_start(stack_switcher, False, True, 0)
        self.pack_start(stack, True, True, 0)


    def populate_store(self, store, elements, roots, info):
        """Populates tree store with data.
        
        Roots are added at first. And then 2 more layers. That is enough
        for disk trees and vgs trees both.
        """
        
        for elem1 in roots:            
            parent_row2 = self.append_row(elem1, store, None, info)                        
            for elem2_uuid in elem1['children']:              
                elem2 = get_by_uuid(elem2_uuid, elements)
                if elem2['type'] == 'pv':
                    break  
                parent_row3 = self.append_row(elem2, store, parent_row2, info)                                                  
                for elem3_uuid in elem2['children']:
                    elem3 = get_by_uuid(elem3_uuid, elements)
                    if elem3['type'] == 'pv':
                        break 
                    parent_row4 = self.append_row(elem3, store, parent_row3, info)                        
                    for elem4_uuid in elem3['children']:
                        elem4 = get_by_uuid(elem4_uuid, elements)
                        if elem4['type'] == 'pv':
                            break
                        self.append_row(elem4, store, parent_row4, info)  


    def append_row(self, elem, store, parent_row, info): 
        """Appends row with given element.
        """        
        icon = self.assign_icon(elem)
        text = elem[info]
        new_parent_row = store.append(parent_row,[icon, text, elem['uuid']])
        return new_parent_row


    def assign_icon(self, elem):
        """Returns appropriate icon for element to display in the tree view.
        """
        icons = self.get_icons()
        icon = icons['free']
                
        if elem['label']['type']['short'] == 'Cache':
            icon = None
        elif elem['label']['type']['short'].startswith('Thin pool'):
            icon = None
        elif elem['label']['type']['short'] == 'VG':    
            icon = None
        elif elem['children']:
            child = get_by_uuid(elem['children'][0], self.all_elems)
            if child['type'] == 'pv':
                icon = icons['pv'] 
            else:
                icon = None
                
        if elem['mountpoint']:
            icon = icons['mount']
        elif elem['fstype'] in FS_TYPES:
            icon = icons['fs']
            
        if elem['fstype'].startswith('LVM'):
            icon = icons['pv']       
        
        return icon


    def get_icons(self):
        """Returns dictionary of icons to use in the tree view.
        """
        pixbuf = GdkPixbuf.Pixbuf()
        dict_icons = {}
        dict_icons['free'] = pixbuf.new_from_file_at_size('graphics/free.png', 10, 10)
        dict_icons['pv'] = pixbuf.new_from_file_at_size('graphics/pv.png', 10, 10)
        dict_icons['mount'] = pixbuf.new_from_file_at_size('graphics/mount.png', 10, 10)
        dict_icons['fs'] = pixbuf.new_from_file_at_size('graphics/fs.jpg', 9, 9)
        return dict_icons


class TreeView(Gtk.TreeView): 
    
    def __init__(self, tree_store, all_elems, window):
        
        self.window = window
        self.all_elems = all_elems
        
        Gtk.TreeView.__init__(self, tree_store)
        self.connect('row_activated', self.on_row_activated)
        self.set_activate_on_single_click(True)
        

    def on_row_activated(self, widget, path, column):
        tree_store = self.get_model()
        it = tree_store.get_iter(path)
        elem_id = tree_store.get_value(it,2)
        
        self.window.info_box.box.destroy()
        self.window.info_box.__init__(self.all_elems, elem_id)
        
        self.window.scheme_box.rectangle[elem_id].emit('focus', False)
        

    