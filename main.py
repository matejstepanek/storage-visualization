'''
Created: 2015

@author: mstepane@redhat.com

Displaying storage layers in GUI.
'''

from gi.repository import Gtk, Gdk   #@UnresolvedImport

from data.data import Elements
from visualization.scheme import SchemeBox
from visualization.info import InfoBox
from visualization.tree import TreeBox
import visualization.actions as actions


class MainWindow(Gtk.Window):
    """Window with GUI.
    """

    def __init__(self):
        """Draws a GUI.
        """
        
        Gtk.Window.__init__(self, default_width=1300, default_height=700, 
                            width_request=400, height_request=400,
                            border_width=5, title='storage visualization')
        
        actions.destroy_children(self)
        
        self.set_css_styles()
        
        elems = Elements()
        self.all_elements = elems.all_elements

        paned = Gtk.Paned()
        self.add(paned)


        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        paned.pack1(main_box, True, True)

        tree_box = TreeBox(self, elems.all_elements, elems.disks_loops, elems.vgs)
        paned.pack2(tree_box, False, True)


        scrolled_scheme_window = Gtk.ScrolledWindow()
        scrolled_scheme_window.set_name('White')
        main_box.pack_start(scrolled_scheme_window, True, True, 0)
        
        scrolled_info_window = Gtk.ScrolledWindow(height_request=110,
                                    vscrollbar_policy=Gtk.PolicyType.NEVER)
        main_box.pack_start(scrolled_info_window, False, False, 0)
        
        
        self.scheme_box = SchemeBox(self, elems.all_elements, elems.pvs,
                                    elems.vgs, elems.lvs, elems.disks_loops)
        scrolled_scheme_window.add(self.scheme_box)        

        centering = Gtk.Alignment(xalign=0.5)
        scrolled_info_window.add(centering)
        
        self.info_box = InfoBox(elems.all_elements)
        centering.add(self.info_box)
        
        
        self.connect('delete-event', Gtk.main_quit)
        self.connect('button-press-event', self.on_button_press)        
        self.show_all()


    def set_css_styles(self):
        """Sets css styles for a whole GUI.
        """
        
        screen = Gdk.Screen.get_default()

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('visualization/styles.css')
        
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)


    def on_button_press(self, widget, event):
        """Click anywhere in GUI removes highlighting of element dependencies.
        """
        
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            
            actions.clear_dependencies(self)
        

if __name__ == '__main__':
    MainWindow()
    Gtk.main()

