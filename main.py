'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage layers in GUI.
'''

from gi.repository import Gtk, Gdk   #@UnresolvedImport

from data.data import Elements
from visualization.scheme import Scheme
from visualization.info_box import InfoBox
from visualization.tree_panel import TreePanel


class MainWindow(Gtk.Window):
    """Window with GUI.
    """

    def __init__(self):
        """Draws a window and displays storage scheme and tree panel in it.
        """
        
        Gtk.Window.__init__(self, default_width=1300, default_height=700, 
                            width_request=400, height_request=400,
                            border_width=5, title='storage visualization')

        self.connect('delete-event', Gtk.main_quit)
        
        self.set_css_styles()
        
        elems = Elements()


        paned = Gtk.Paned()
        self.add(paned)


        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        paned.pack1(left_box, True, True)

        panel = TreePanel(self, elems.all_elems, elems.vgs, elems.lvs,
                          elems.disks_loops)
        paned.pack2(panel, False, True)


        scrolled_scheme_window = Gtk.ScrolledWindow()
        scrolled_scheme_window.set_name('White')
        left_box.pack_start(scrolled_scheme_window, True, True, 0)
        
        scrolled_info_window = Gtk.ScrolledWindow(height_request=110,
                                    vscrollbar_policy=Gtk.PolicyType.NEVER)
        left_box.pack_start(scrolled_info_window, False, False, 0)
        
        
        self.scheme_box = Scheme(self, elems.all_elems, elems.pvs, elems.vgs,
                                 elems.lvs, elems.disks_loops)
        scrolled_scheme_window.add(self.scheme_box)        

        self.info_box = InfoBox(elems.all_elems)
        scrolled_info_window.add(self.info_box)
        
        
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

