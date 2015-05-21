'''
Created: 2015

@author: mstepane@redhat.com

Rectangle representing one storage element.
'''

from gi.repository import Gtk, Pango, Gdk #@UnresolvedImport

from icons import Icons
from data.utils import get_by_uuid
import actions
import menus


MIN_WIDTH = 110
MAX_WIDTH = 500


class Rectangle(Gtk.Button):
    """Rectangle representing one storage element (disk, volume group, LV, ...)
    """
    
    __gtype_name__ = 'Rectangle'
    
    
    def __init__(self, element, main_window):
        """Initiates rectangle with appropriate size, icons and label.
        """
        
        self.all_elements = main_window.all_elements
        self.main_window = main_window
        self.uuid = element['uuid']
        
        width = self.get_width(element)
        
        Gtk.Button.__init__(self, width_request = width, height_request=50)
   
        if element['type'] == 'lv':
            self.set_size_request(width, 60)
         
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5,
                       margin_top=2, margin_bottom=2)
        self.add(vbox)
        
        hbox = Gtk.Box(spacing=4)
        vbox.pack_start(hbox, False, False, 0)
        
        self.left_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        hbox.pack_start(self.left_vbox, False, False, 0)
            
        label = self.get_label(element)
        hbox.pack_start(label, True, True, 0)
        
        self.add_left_icons(element, self.left_vbox)
        
        
        if element['type'] == 'lv':
            if element['is_origin'] or (element['origin'] and element['segtype'] != 'cache'):
                self.set_color_box(hbox)
        
        if element['occupied'] >= 0:
            self.set_progress_bar(element['occupied'], vbox)


        self.connect('button-press-event', self.on_button_press)
    
    
    def get_width(self, element):
        """Returns width of the rectangle in pixels.
        
        I don't want too wide disks. VG is ok, cause its width depends on
        its logical volumes.
        """

        giga_size = int(round(element['size'] / 1000000000.0))
        
        if giga_size < MIN_WIDTH:
            width = MIN_WIDTH
            
        elif giga_size > MAX_WIDTH and element['type'] != 'vg':
            width = MAX_WIDTH
            
        else:
            width = giga_size
            
        return width

    
    def get_label(self, element):
        """Returns appropriate label for a given element.
        """
        
        markup = '<b>%s</b>\n<small>%s</small>' %(element['label']['name'],
                                                  element['label']['type']['short'])
        label = Gtk.Label(justify=Gtk.Justification.CENTER, max_width_chars=5,                          
                        ellipsize=Pango.EllipsizeMode.END)
        label.set_markup(markup)
        
        return label
    

    def add_left_icons(self, element, box):
        """Adds appropriate icons to the top left corner of the rectangle.
        """
        
        icons = Icons(self.all_elements)
        icon = icons.assign_icon(element)
        
        if element['encrypted']:
            image_crypt = Gtk.Image.new_from_pixbuf(icons.crypt)
            box.pack_start(image_crypt, False, False, 0)
                
        if icon:
            image = Gtk.Image.new_from_pixbuf(icon)        
            box.pack_start(image, False, False, 0)
            

    def set_color_box(self, hbox):
        """Adds a color box for highlighting snapshots and their origins.
        """
        
        self.color_box = Gtk.Frame(width_request=6)
        self.color_box.set_shadow_type(Gtk.ShadowType.NONE)
        hbox.pack_start(self.color_box, False, False, 0)
    
    
    def set_progress_bar(self, occupied, vbox):
        """Adds a progress bar that shows amount of the occupied space.
        """
        
        text = '%.0f %% occupied' % occupied
        
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(occupied/100)
        progress_bar.set_text(text)
        progress_bar.set_show_text(True)
        
        vbox.pack_start(progress_bar, False, False, 0)
    

####### ON RECTANGLE PRESS ####################################################

    def on_button_press(self, widget, event):
        """ Double left click - show dependencies.
            Single click - clear dependencies, higlight this rectangle.
                if right click - show popup menu.
        """
        
        element = get_by_uuid(self.uuid, self.all_elements)
        
        if event.button == 3:  # right click
            
            actions.clear_dependencies(self.main_window)

            self.main_window.scheme_box.rectangles[self.uuid].emit('activate')

            self.main_window.scheme_box.rectangles[self.uuid].emit('focus', False)
             
            self.main_window.info_box.__init__(self.all_elements, self.uuid)
            
            self.menu = menus.get_menu(element, self.main_window)
            self.menu.popup(None, None, None, None, event.button, event.time)

            
        elif event.type == Gdk.EventType._2BUTTON_PRESS:  # double click
            self.draw_dependencies()
            
            
        else:
            actions.clear_dependencies(self.main_window)
            self.main_window.info_box.__init__(self.all_elements, self.uuid)
    

    def draw_dependencies(self):
        """Highlights all rectangles that are dependent on the pressed one.
        """
        
        rectangles = self.main_window.scheme_box.rectangles
        
        element = get_by_uuid(self.uuid, self.all_elements)
        
        dependencies = []
        
        if element:
            if element['parents']:
                self.append_ancestors(element, dependencies)
                
            if element['children']:
                self.append_descendants(element, dependencies)
                
            for uuid in rectangles:
                if uuid in dependencies:
                    rectangles[uuid].set_name('Highlighted')
            

    def append_ancestors(self, element, dependencies):
        """Recursively appends all ancestors of a given element.
        """
        
        for parent_uuid in element['parents']:
            
            dependencies.append(parent_uuid)
            
            parent = get_by_uuid(parent_uuid,self.all_elements)
            
            if parent and parent['parents']:
                self.append_ancestors(parent, dependencies)
        
        
    def append_descendants(self, element, dependencies):
        """Recursively appends all descendants of a given element.
        """
        
        for child_uuid in element['children']:
            
            dependencies.append(child_uuid)
            
            child = get_by_uuid(child_uuid,self.all_elements)
            
            if child and child['children']:
                self.append_descendants(child, dependencies)
                
