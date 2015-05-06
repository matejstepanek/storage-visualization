'''
Created: 2015

@author: mstepane@redhat.com

Rectangle representing one storage element.
'''

from gi.repository import Gtk, Pango, Gdk #@UnresolvedImport
import subprocess

from icons import Icons
from data.utils import get_by_uuid

MIN_WIDTH = 110
MAX_WIDTH = 500


class Rectangle(Gtk.Button):
    """Rectangle representing one storage element (disk, volume group, LV, ...)
    """
    
    __gtype_name__ = 'Rectangle'
    
    
    def __init__(self, element, all_elements, main_window):
        """Initiates rectangle with appropriate size, icons and label.
        """
        
        self.all_elements = all_elements
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
        
        self.left_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5,
                                 width_request=9)
        hbox.pack_start(self.left_vbox, False, False, 0)
            
        label = self.get_label(element)
        hbox.pack_start(label, True, True, 0)
        
        self.right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(self.right_vbox, False, False, 0)
        
        icons = Icons(self.all_elements)
        self.add_left_icons(element, icons, self.left_vbox)
        self.add_right_icons(element, icons, self.right_vbox)
        
        if element['type'] == 'lv' and (element['is_origin'] or (element['origin'] and element['segtype'] != 'cache')):
            self.set_color_box(vbox)
        
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
    

    def add_left_icons(self, elem, icons, box):
        """Adds appropriate icons to the top left corner of the rectangle.
        """
        
        icon = icons.assign_icon(elem)
            
        if icon:
            image = Gtk.Image.new_from_pixbuf(icon)        
            box.pack_start(image, False, False, 0)
            
        if elem['encrypted']:
            image_crypt = Gtk.Image.new_from_pixbuf(icons.crypt)
            box.pack_start(image_crypt, False, False, 0)
            

    def add_right_icons(self, element, icons, box):
        """Adds appropriate icons to the top right corner of the rectangle.
        """
        
        image_menu = Gtk.Image.new_from_pixbuf(icons.menu)
        box.pack_start(image_menu, False, False, 0)
        
    
    def set_color_box(self, vbox):
        """Adds a color box for highlighting snapshots and their origins.
        """
        
        self.color_box = Gtk.Frame(height_request=6)
        self.color_box.set_shadow_type(Gtk.ShadowType.NONE)
        vbox.pack_start(self.color_box, False, False, 0)
    
    
    def set_progress_bar(self, occupied, vbox):
        """Returns progress bar that shows amount of the occupied space.
        """
        
        text = '%.0f %% occupied' % occupied
        
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(occupied/100)
        progress_bar.set_text(text)
        progress_bar.set_show_text(True)
        
        vbox.pack_start(progress_bar, False, False, 0)
    

    def on_button_press(self, widget, event):

        element = get_by_uuid(self.uuid, self.all_elements)
        
        if event.button == 3:   # 3 means right mouse button
            
            if element['name'] == 'loop3' and element['type'] == 'loop':

                self.menu = Gtk.Menu()
                menuitem1 = Gtk.MenuItem('Format')
                menuitem2 = Gtk.MenuItem('Encrypt')
                menuitem3 = Gtk.MenuItem('Create PV')
                menuitem4 = Gtk.MenuItem('Detach')
                self.menu.append(menuitem1)
                self.menu.append(menuitem2)
                self.menu.append(menuitem3)
                self.menu.append(menuitem4)
                self.menu.connect('button-press-event', self.pvcreate)

                self.menu.popup(None, None, None, None, event.button, event.time)
                self.menu.show_all()
                
                
            elif element['label']['name'] == 'loop3' and element['type'] == 'pv':
                
                self.menu = Gtk.Menu()
                menuitem1 = Gtk.MenuItem('Add to VG alpha')
                menuitem2 = Gtk.MenuItem('Add to VG fedora')
                menuitem3 = Gtk.MenuItem('Remove')
                self.menu.append(menuitem1)
                self.menu.append(menuitem2)
                self.menu.append(menuitem3)
                self.menu.connect('button-press-event', self.vgextend)

                self.menu.popup(None, None, None, None, event.button, event.time)
                self.menu.show_all()
                 
            elif element['name'] == 'sda':
                
                subprocess.check_output(['sudo', 'vgreduce', 'alpha', '/dev/loop3'])
                subprocess.check_output(['sudo', 'pvremove', '/dev/loop3'])
                self.main_window.__init__()
                
                
        elif event.type == Gdk.EventType._2BUTTON_PRESS:    # double click
            self.draw_dependencies()
            
        else:
            self.clear_dependencies()
            self.main_window.info_box.__init__(self.all_elements, self.uuid)
    
    
    def pvcreate(self, widget, event):
        
        subprocess.check_output(['sudo', 'pvcreate', '/dev/loop3'])
        self.main_window.__init__()
        

    def vgextend(self, widget, event):
        
        subprocess.check_output(['sudo', 'vgextend', 'alpha', '/dev/loop3'])
        self.main_window.__init__()
    
        
    def draw_dependencies(self):
        
        rectangle = self.main_window.scheme_box.rectangle
        
        elem = get_by_uuid(self.uuid, self.all_elements)
        
        dependencies = [self.uuid]
        
        if elem['parents']:
            self.append_ancestors(elem, dependencies)
            
        if elem['children']:
            self.append_descendants(elem, dependencies)
            
        for uuid in rectangle:
            if uuid in dependencies:
                rectangle[uuid].set_name('Dependency')
            

    def append_ancestors(self, elem, dependencies):
        """Recursively appends all ancestors of a given element.
        """
        
        for parent_uuid in elem['parents']:
            
            dependencies.append(parent_uuid)
            
            parent = get_by_uuid(parent_uuid,self.all_elements)
            
            if parent and parent['parents']:
                self.append_ancestors(parent, dependencies)
        
        
    def append_descendants(self, elem, dependencies):
        """Recursively appends all descendants of a given element.
        """
        
        for child_uuid in elem['children']:
            
            dependencies.append(child_uuid)
            
            child = get_by_uuid(child_uuid,self.all_elements)
            
            if child and child['children']:
                self.append_descendants(child, dependencies)
                
    
    def clear_dependencies(self):
        
        rectangle = self.main_window.scheme_box.rectangle
        for rec in rectangle.itervalues():
            rec.set_name('Rectangle')
            
