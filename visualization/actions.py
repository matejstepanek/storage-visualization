'''
Created: 2015

@author: mstepane@redhat.com

Actions to perform when various signals are emitted.
'''

from gi.repository import Gtk   #@UnresolvedImport


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


class Menu(Gtk.Menu):
    """Popup context menu for storage elements.
    """
    
    def __init__(self, element, main_window):

        Gtk.Menu.__init__(self)
        
        self.main_window = main_window
        
        items = [('Action 1', self.first),
                 ('Action 2', self.second)]
        
        for item in items:
            
            menu_item = Gtk.MenuItem(item[0])
            menu_item.connect('activate', item[1])
            self.add(menu_item)

        self.show_all()
    
    
    def first(self, menu_item):
        
        self.main_window.__init__()
        print 'Action 1'


    def second(self, menu_item):
        
        self.main_window.__init__()                   
        print 'Action 2'

