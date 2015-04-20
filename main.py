'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage layers in GUI.
'''

from gi.repository import Gtk, Gdk   #@UnresolvedImport

from data.data import Elements
from visualization.scheme import Scheme
from visualization.tree_panel import TreePanel


class MainWindow(Gtk.Window):
    """Window with GUI.
    """

    def __init__(self):
        """Draws a window and displays storage scheme and tree panel in it.
        """
        Gtk.Window.__init__(self, default_width=1400, default_height=700, 
                            width_request=400, height_request=500,
                            border_width=5, title='storage visualization')

        self.connect('delete-event', Gtk.main_quit)
        
        self.set_css_styles()
        
        elems = Elements()
              
        self.paned = Gtk.Paned()
        self.add(self.paned)
    
        self.scheme_box = Scheme(self, elems.all_elems, elems.pvs, elems.vgs,
                                 elems.lvs, elems.disks_loops)
        self.paned.pack1(self.scheme_box, True, False)        

        panel = TreePanel(self, elems.all_elems, elems.vgs, elems.lvs,
                          elems.disks_loops)
        self.paned.pack2(panel, False, True)
        
        self.show_all()


    def set_css_styles(self):
        screen = Gdk.Screen.get_default()

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('visualization/styles.css')
        
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)


if __name__ == '__main__':
    MainWindow()
    Gtk.main()

