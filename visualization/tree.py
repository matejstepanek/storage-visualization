'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage elements in dependency trees.
'''

from gi.repository import Gtk, GdkPixbuf   #@UnresolvedImport

from data.utils import get_by_uuid
from icons import Icons


class TreeBox(Gtk.Box):
    """Box with tree structure of storage elements.
    """
    
    def __init__(self, main_window, all_elements, disks_loops, vgs):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        
        self.icons = Icons(all_elements)
        mountpoints = self.get_mountpoints(all_elements)
        
        stack = Gtk.Stack()
        
        store_disks = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_disks, disks_loops, all_elements, 'name')
        view_disks = self.get_tree_view(store_disks, all_elements, main_window)
        stack.add_titled(view_disks, 'disks', 'Disks')
        
        store_vgs = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_vgs, vgs, all_elements, 'name')
        view_vgs = self.get_tree_view(store_vgs, all_elements, main_window)
        stack.add_titled(view_vgs, 'vgs', 'Volume groups')
        
        store_mountpoints = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_mountpoints, mountpoints, all_elements, 'mountpoint')
        view_mountpoints = self.get_tree_view(store_mountpoints, all_elements, main_window)
        stack.add_titled(view_mountpoints, 'mountpoints', 'Mount points')
        
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        self.pack_start(stack_switcher, False, True, 0)
        self.pack_start(stack, True, True, 0)
        
        
    def get_mountpoints(self, all_elements):
        """Returns storage elements with mounted file systems.
        """
        
        mountpoints = []
        
        for elem in all_elements:
            if elem['mountpoint']:
                mountpoints.append(elem)
            
        return mountpoints

    
    def populate_store(self, store, roots, elements, info):
        """Populates tree store with data.
        
        Roots are added at first. And then 3 more layers.
        """
        
        for elem1 in roots:
            
            parent_row1 = self.append_row(elem1, store, None, info)                        
            
            
            for elem2_uuid in elem1['children']:
                
                elem2 = get_by_uuid(elem2_uuid, elements)
                if elem2 and elem2['type'] != 'pv':
                    parent_row2 = self.append_row(elem2, store, parent_row1, info)
                else:
                    break
                
                
                for elem3_uuid in elem2['children']:
                    
                    elem3 = get_by_uuid(elem3_uuid, elements)
                    if elem3 and elem3['type'] != 'pv':
                        parent_row3 = self.append_row(elem3, store, parent_row2, info)
                    else:
                        break
                    
                    
                    for elem4_uuid in elem3['children']:
                        
                        elem4 = get_by_uuid(elem4_uuid, elements)
                        if elem4 and elem4['type'] != 'pv':                        
                            self.append_row(elem4, store, parent_row3, info)
                        else:
                            break


    def append_row(self, element, store, parent_row, info): 
        """Appends row with a given element.
        """
        
        icon = self.icons.assign_icon(element)
        
        text = element[info]
        new_parent_row = store.append(parent_row,[icon, text, element['uuid']])
        
        return new_parent_row


    def get_tree_view(self, tree_store, all_elements, main_window):
        """Returns tree view based on the given tree store.
        """
        
        tree_view = TreeView(tree_store, all_elements, main_window)
        tree_view.set_headers_visible(False)
        tree_view.set_enable_tree_lines(True)
        
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        tree_view.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('', renderer_text, text=1)
        tree_view.append_column(column_text)
              
        scrolled_window_view = Gtk.ScrolledWindow()
        scrolled_window_view.add(tree_view)
        
        return scrolled_window_view


class TreeView(Gtk.TreeView): 
    
    def __init__(self, tree_store, all_elements, main_window):
        
        Gtk.TreeView.__init__(self, tree_store)
        
        self.all_elements = all_elements
        self.main_window = main_window
        
        self.connect('row_activated', self.on_row_activated)
        self.set_activate_on_single_click(True)
        

    def on_row_activated(self, widget, path, column):
        
        tree_store = self.get_model()
        it = tree_store.get_iter(path)
        elem_id = tree_store.get_value(it,2)
        
        self.main_window.info_box.__init__(self.all_elements, elem_id)
        
        self.main_window.scheme_box.rectangle[elem_id].emit('focus', False)
        
    