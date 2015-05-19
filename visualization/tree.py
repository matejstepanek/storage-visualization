'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage elements in dependency trees.
'''

from gi.repository import Gtk, Gdk, GdkPixbuf   #@UnresolvedImport

from data.utils import get_by_uuid
from icons import Icons
import actions
import menus


class TreeBox(Gtk.Box):
    """Box with tree structure of storage elements.
    """
    
    def __init__(self, main_window, all_elements, disks_loops, vgs):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                         width_request=280)
        
        self.icons = Icons(all_elements)
        
        actions.destroy_children(self)
        
        
        stack = Gtk.Stack()
        
        store_disks = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str, str)
        self.populate_store(store_disks, disks_loops, all_elements)
        view_disks = self.get_tree_view(store_disks, all_elements, main_window)
        stack.add_titled(view_disks, 'disks', 'Disks')
        
        store_vgs = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str, str)
        self.populate_store(store_vgs, vgs, all_elements)
        view_vgs = self.get_tree_view(store_vgs, all_elements, main_window)
        stack.add_titled(view_vgs, 'vgs', 'Volume groups')
        
      
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        self.pack_start(stack_switcher, False, True, 0)
        self.pack_start(stack, True, True, 0)
        
    
    def populate_store(self, store, roots, elements):
        """Populates tree store with data.
        
        Roots are added at first and then other layers.
        """
        
        for root in roots:
            
            parent_row = self.append_row(root, store, None)
            
            self.recursively_append_children(root, elements, store, parent_row)


    def append_row(self, element, store, parent_row): 
        """Appends row with a given element.
        """
        
        icon = self.icons.assign_icon(element)
        
        text = '%s' %element['label']['type']['short']
        
        if element['type'] == 'pv' and element['vg_name']:
            text += ' in VG %s' %element['vg_name']
        
        new_parent_row = store.append(parent_row,[icon, element['label']['name'],
                                                  text, element['uuid']])
        
        return new_parent_row
        
    
    def recursively_append_children(self, parent, elements, store, parent_row):
        """Appends all children of a given parent element.
        """
        
        for child_uuid in parent['children']:
                
                child = get_by_uuid(child_uuid, elements)
                
                if child and child['type'] != 'vg':
                    new_parent_row = self.append_row(child, store, parent_row)
                else:
                    break
                
                self.recursively_append_children(child, elements, store,
                                                 new_parent_row)
    

    def get_tree_view(self, tree_store, all_elements, main_window):
        """Returns tree view based on the given tree store.
        """
        
        tree_view = TreeView(tree_store, all_elements, main_window)
        tree_view.set_enable_tree_lines(True)
        
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(None, renderer_pixbuf, pixbuf=0)
        tree_view.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Name', renderer_text, text=1)
        tree_view.append_column(column_text)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Type', renderer_text, text=2)
        tree_view.append_column(column_text)
              
        scrolled_window_view = Gtk.ScrolledWindow()
        scrolled_window_view.add(tree_view)
        
        return scrolled_window_view
    

class TreeView(Gtk.TreeView): 
    
    def __init__(self, tree_store, all_elements, main_window):
        
        Gtk.TreeView.__init__(self, tree_store)
        
        self.all_elements = all_elements
        self.main_window = main_window
        
        self.connect('button-press-event', self.on_button_press)

    
    def on_button_press(self, tree_view, event):
        """Click on menu item:
            if double left - highlight corresponding rectangle.
            if right - show popup menu.
        """
        
        actions.clear_dependencies(self.main_window)
        self.main_window.info_box.__init__(self.all_elements)
        
        if event.type == Gdk.EventType._2BUTTON_PRESS:  # double left click

            row = tree_view.get_path_at_pos(int(event.x), int(event.y))    
            
            if row:
                
                uuid = self.get_uuid(row[0], tree_view)
                
                self.main_window.info_box.__init__(self.all_elements, uuid)
                actions.clear_dependencies(self.main_window)
                self.main_window.scheme_box.rectangles[uuid].emit('focus', False)
                
        elif event.button == 3:  # right click
            
            row = tree_view.get_path_at_pos(int(event.x), int(event.y))    
            
            if row:
                
                uuid = self.get_uuid(row[0], tree_view)
                element = get_by_uuid(uuid, self.all_elements)
                
                self.menu = menus.get_menu(element, self.main_window)
                self.menu.popup(None, None, None, None, event.button, event.time)
            

    def get_uuid(self, path, tree_view):
        """Returns uuid of the row on the given path.
        """
        
        tree_store = tree_view.get_model()
        iterator = tree_store.get_iter(path)
        uuid = tree_store.get_value(iterator,3)
        
        return uuid

