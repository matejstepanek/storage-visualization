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
        
        width = self.get_width(element)
        
        Gtk.Button.__init__(self, width_request = width, height_request=50)
   
        if element['type'] == 'lv':
            self.set_size_request(width, 60)
            
        self.uuid = element['uuid']
         
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
        if event.button == 3:
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
                self.menu.connect('button-press-event', self.menu_press_1)

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
                self.menu.connect('button-press-event', self.menu_press_2)

                self.menu.popup(None, None, None, None, event.button, event.time)
                self.menu.show_all()
                 
            elif element['name'] == 'sda':
                if True:
                    subprocess.check_output(['sudo', 'vgreduce', 'alpha', '/dev/loop3'])
                    subprocess.check_output(['sudo', 'pvremove', '/dev/loop3'])
                    self.main_window.paned.destroy()
                    self.main_window.__init__()
                    
        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            self.draw_dependencies()
        else:
            rectangle = self.main_window.scheme_box.rectangle
            for rec in rectangle.itervalues():
                rec.set_name('Rectangle') 
            self.main_window.info_box.__init__(self.all_elements, self.uuid)
    
    
    def menu_press_1(self, widget, event):
        
        subprocess.check_output(['sudo', 'pvcreate', '/dev/loop3'])
        self.main_window.paned.destroy()
        self.main_window.__init__()
        

    def menu_press_2(self, widget, event):
        
        subprocess.check_output(['sudo', 'vgextend', 'alpha', '/dev/loop3'])
        self.main_window.paned.destroy()
        self.main_window.__init__()
    
        
    def draw_dependencies(self):
        
        rectangle = self.main_window.scheme_box.rectangle
        dependencies = self.get_dependencies()
        for uuid in rectangle:
            if uuid in dependencies:
                rectangle[uuid].set_name('Dependency')
            

    def get_dependencies(self):
 
        elem = get_by_uuid(self.uuid, self.all_elements)
        dependencies = [self.uuid]
        
        # Appends parents and grandparents and so on.
        for p_uuid in elem['parents']:
            dependencies.append(p_uuid)
            p = get_by_uuid(p_uuid,self.all_elements)
            for p1_uuid in p['parents']:
                dependencies.append(p1_uuid)
                p1 = get_by_uuid(p1_uuid,self.all_elements)
                for p2_uuid in p1['parents']:
                    dependencies.append(p2_uuid)
                    p2 = get_by_uuid(p2_uuid,self.all_elements)
                    for p3_uuid in p2['parents']:
                        dependencies.append(p3_uuid)
                        p3 = get_by_uuid(p3_uuid,self.all_elements)
                        for p4_uuid in p3['parents']:
                            dependencies.append(p4_uuid)
                            p4 = get_by_uuid(p4_uuid,self.all_elements)
                            for p5_uuid in p4['parents']:
                                dependencies.append(p5_uuid)
                                p5 = get_by_uuid(p5_uuid,self.all_elements)
                                for p6_uuid in p5['parents']:
                                    dependencies.append(p6_uuid)
                                    p6 = get_by_uuid(p6_uuid,self.all_elements)
                                    for p7_uuid in p6['parents']:
                                        dependencies.append(p7_uuid)
                                        p7 = get_by_uuid(p7_uuid,self.all_elements)
                                        for p8_uuid in p7['parents']:
                                            dependencies.append(p8_uuid)
                                            p8 = get_by_uuid(p8_uuid,self.all_elements)
                                            for p9_uuid in p8['parents']:
                                                dependencies.append(p9_uuid)
                                                p9 = get_by_uuid(p9_uuid,self.all_elements)
                                                for p10_uuid in p9['parents']:
                                                    dependencies.append(p10_uuid)
        # Appends children, grandchildren and so on.
        for p_uuid in elem['children']:
            dependencies.append(p_uuid)
            p = get_by_uuid(p_uuid,self.all_elements)
            for p1_uuid in p['children']:
                dependencies.append(p1_uuid)
                p1 = get_by_uuid(p1_uuid,self.all_elements)
                for p2_uuid in p1['children']:
                    dependencies.append(p2_uuid)
                    p2 = get_by_uuid(p2_uuid,self.all_elements)
                    for p3_uuid in p2['children']:
                        dependencies.append(p3_uuid)
                        p3 = get_by_uuid(p3_uuid,self.all_elements)
                        for p4_uuid in p3['children']:
                            dependencies.append(p4_uuid)
                            p4 = get_by_uuid(p4_uuid,self.all_elements)
                            for p5_uuid in p4['children']:
                                dependencies.append(p5_uuid)
                                p5 = get_by_uuid(p5_uuid,self.all_elements)
                                for p6_uuid in p5['children']:
                                    dependencies.append(p6_uuid)
                                    p6 = get_by_uuid(p6_uuid,self.all_elements)
                                    for p7_uuid in p6['children']:
                                        dependencies.append(p7_uuid)
                                        p7 = get_by_uuid(p7_uuid,self.all_elements)
                                        for p8_uuid in p7['children']:
                                            dependencies.append(p8_uuid)
                                            p8 = get_by_uuid(p8_uuid,self.all_elements)
                                            for p9_uuid in p8['children']:
                                                dependencies.append(p9_uuid)
                                                p9 = get_by_uuid(p9_uuid,self.all_elements)
                                                for p10_uuid in p9['children']:
                                                    dependencies.append(p10_uuid)
        
        return dependencies

