'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage elements in dependency trees.
'''

from gi.repository import Gtk, GdkPixbuf   #@UnresolvedImport

from data.utils import get_by_uuid
from icons import Icons
import visualization.actions as actions


class TreeBox(Gtk.Box):
    """Box with tree structure of storage elements.
    """
    
    def __init__(self, main_window, all_elements, disks_loops, vgs):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        
        actions.destroy_children(self)
        
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
        
        Roots are added at first and then other layers.
        """
        
        for root in roots:
            
            parent_row = self.append_row(root, store, None, info)
            
            self.recursively_append_children(root, elements, store, parent_row, info)


    def append_row(self, element, store, parent_row, info): 
        """Appends row with a given element.
        """
        
        icon = self.icons.assign_icon(element)
        
        text = element[info]
        new_parent_row = store.append(parent_row,[icon, text, element['uuid']])
        
        return new_parent_row
        
    
    def recursively_append_children(self, parent, elements, store, parent_row, info):
        """Appends all children of a given parent element.
        """
        
        for child_uuid in parent['children']:
                
                child = get_by_uuid(child_uuid, elements)
                
                if child and child['type'] != 'pv':
                    new_parent_row = self.append_row(child, store, parent_row, info)
                else:
                    break
                
                self.recursively_append_children(child, elements, store,
                                                 new_parent_row, info)
    

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
        
        self.connect('button-press-event', self.on_button_press)
        
        
    def on_row_activated(self, widget, path, column):
        
        tree_store = self.get_model()
        it = tree_store.get_iter(path)
        elem_id = tree_store.get_value(it,2)
        
        self.main_window.info_box.__init__(self.all_elements, elem_id)
        actions.clear_dependencies(self.main_window)
        self.main_window.scheme_box.rectangles[elem_id].emit('focus', False)
        
    def on_button_press(self, widget, event):
        
        self.main_window.info_box.__init__(self.all_elements)
        actions.clear_dependencies(self.main_window)
        
