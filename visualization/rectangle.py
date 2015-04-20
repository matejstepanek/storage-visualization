'''
Created: 2015

@author: mstepane@redhat.com

Rectangle representing one storage element.
'''

from gi.repository import Gtk, Pango, Gdk, GdkPixbuf #@UnresolvedImport
import subprocess

from data.utils import get_by_uuid

FS_TYPES = ['ext3', 'ext4', 'vfat', 'ntfs', 'btrfs', 'xfs']
MIN_WIDTH = 110
MAX_WIDTH = 500


class Rectangle(Gtk.Button):
    """Rectangle representing one storage element (disk, volume group, LV, ...)
    """
    
    __gtype_name__ = 'Rectangle'
    
    def __init__(self, elem, all_elems, window):
        """Initiates rectangle with appropriate size, icons and label.
        """
        
        self.window = window
        self.all_elems = all_elems
        width = self.get_width(elem)
        
        Gtk.Button.__init__(self, width_request = width, height_request=50)
   
        if elem['type'] == 'lv':
            self.set_size_request(width, 60)
            
        self.uuid = elem['uuid']
         
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5,
                       margin_top=2, margin_bottom=2)
        self.add(vbox)
        
        hbox = Gtk.Box(spacing=4)
        vbox.pack_start(hbox, False, False, 0)
        
        self.left_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5,
                                 width_request=9)
        hbox.pack_start(self.left_vbox, False, False, 0)
            
        label = self.get_label(elem)
        hbox.pack_start(label, True, True, 0)
        
        self.right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(self.right_vbox, False, False, 0)
        
        icons = self.get_icons()
        self.add_left_icons(elem, icons, self.left_vbox)
        self.add_right_icons(elem, icons, self.right_vbox)
        
        # color box for snapshots and their origins
        if elem['type'] == 'lv' and (elem['is_origin'] or (elem['origin'] and elem['segtype'] != 'cache')):
            self.color_box = Gtk.Frame(height_request=6)
            self.color_box.set_shadow_type(Gtk.ShadowType.NONE)
            vbox.pack_start(self.color_box, False, False, 0)
        
        # free space progress bar for vgs
        if elem['type'] == 'vg':
            occupied = (1 - (float(elem['vg_free']) / elem['size'])) * 100
            progress_bar = self.get_progress_bar(occupied)
            vbox.pack_start(progress_bar, False, False, 0)
        # free space progress bar for snapshots, thin pools and thin LVs
        elif elem['type'] == 'lv' and elem['data_percent'] >= 0:
            progress_bar = self.get_progress_bar(elem['data_percent'])
            vbox.pack_end(progress_bar, False, False, 0)
        # free space progress bar for mounted file systems
        elif elem['mountpoint'] and elem['fsoccupied'] >= 0:
            progress_bar = self.get_progress_bar(elem['fsoccupied'])
            vbox.pack_end(progress_bar, False, False, 0)
            
        self.connect('button-press-event', self.on_button_press)

      
    def menu_press_1(self, widget, event):
        
        subprocess.check_output(['sudo', 'pvcreate', '/dev/loop3'])
        self.window.paned.destroy()
        self.window.__init__()
        

    def menu_press_2(self, widget, event):
        
        subprocess.check_output(['sudo', 'vgextend', 'alpha', '/dev/loop3'])
        self.window.paned.destroy()
        self.window.__init__()
    

    def on_button_press(self, widget, event):

        elem = get_by_uuid(self.uuid, self.all_elems)
        if event.button == 3:
            if elem['name'] == 'loop3' and elem['type'] == 'loop':

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
                
                
            elif elem['label']['name'] == 'loop3' and elem['type'] == 'pv':
                
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
                 
            elif elem['name'] == 'sda':
                if True:
                    subprocess.check_output(['sudo', 'vgreduce', 'alpha', '/dev/loop3'])
                    subprocess.check_output(['sudo', 'pvremove', '/dev/loop3'])
                    self.window.paned.destroy()
                    self.window.__init__()
                    
        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            self.draw_dependencies()
        else:
            rectangle = self.window.scheme_box.rectangle
            for rec in rectangle.itervalues():
                rec.set_name('Rectangle') 
            self.window.scheme_box.info_box.box.destroy()
            self.window.scheme_box.info_box.__init__(self.all_elems, self.uuid)
    

    def draw_dependencies(self):
        
        rectangle = self.window.scheme_box.rectangle
        dependencies = self.get_dependencies()
        for uuid in rectangle:
            if uuid in dependencies:
                rectangle[uuid].set_name('Dependency')
            

    def get_dependencies(self):
 
        elem = get_by_uuid(self.uuid, self.all_elems)
        dependencies = [self.uuid]
        
        # Appends parents and grandparents and so on.
        for p_uuid in elem['parents']:
            dependencies.append(p_uuid)
            p = get_by_uuid(p_uuid,self.all_elems)
            for p1_uuid in p['parents']:
                dependencies.append(p1_uuid)
                p1 = get_by_uuid(p1_uuid,self.all_elems)
                for p2_uuid in p1['parents']:
                    dependencies.append(p2_uuid)
                    p2 = get_by_uuid(p2_uuid,self.all_elems)
                    for p3_uuid in p2['parents']:
                        dependencies.append(p3_uuid)
                        p3 = get_by_uuid(p3_uuid,self.all_elems)
                        for p4_uuid in p3['parents']:
                            dependencies.append(p4_uuid)
                            p4 = get_by_uuid(p4_uuid,self.all_elems)
                            for p5_uuid in p4['parents']:
                                dependencies.append(p5_uuid)
                                p5 = get_by_uuid(p5_uuid,self.all_elems)
                                for p6_uuid in p5['parents']:
                                    dependencies.append(p6_uuid)
                                    p6 = get_by_uuid(p6_uuid,self.all_elems)
                                    for p7_uuid in p6['parents']:
                                        dependencies.append(p7_uuid)
                                        p7 = get_by_uuid(p7_uuid,self.all_elems)
                                        for p8_uuid in p7['parents']:
                                            dependencies.append(p8_uuid)
                                            p8 = get_by_uuid(p8_uuid,self.all_elems)
                                            for p9_uuid in p8['parents']:
                                                dependencies.append(p9_uuid)
                                                p9 = get_by_uuid(p9_uuid,self.all_elems)
                                                for p10_uuid in p9['parents']:
                                                    dependencies.append(p10_uuid)
        # Appends children, grandchildren and so on.
        for p_uuid in elem['children']:
            dependencies.append(p_uuid)
            p = get_by_uuid(p_uuid,self.all_elems)
            for p1_uuid in p['children']:
                dependencies.append(p1_uuid)
                p1 = get_by_uuid(p1_uuid,self.all_elems)
                for p2_uuid in p1['children']:
                    dependencies.append(p2_uuid)
                    p2 = get_by_uuid(p2_uuid,self.all_elems)
                    for p3_uuid in p2['children']:
                        dependencies.append(p3_uuid)
                        p3 = get_by_uuid(p3_uuid,self.all_elems)
                        for p4_uuid in p3['children']:
                            dependencies.append(p4_uuid)
                            p4 = get_by_uuid(p4_uuid,self.all_elems)
                            for p5_uuid in p4['children']:
                                dependencies.append(p5_uuid)
                                p5 = get_by_uuid(p5_uuid,self.all_elems)
                                for p6_uuid in p5['children']:
                                    dependencies.append(p6_uuid)
                                    p6 = get_by_uuid(p6_uuid,self.all_elems)
                                    for p7_uuid in p6['children']:
                                        dependencies.append(p7_uuid)
                                        p7 = get_by_uuid(p7_uuid,self.all_elems)
                                        for p8_uuid in p7['children']:
                                            dependencies.append(p8_uuid)
                                            p8 = get_by_uuid(p8_uuid,self.all_elems)
                                            for p9_uuid in p8['children']:
                                                dependencies.append(p9_uuid)
                                                p9 = get_by_uuid(p9_uuid,self.all_elems)
                                                for p10_uuid in p9['children']:
                                                    dependencies.append(p10_uuid)
        
        return dependencies


    def get_width(self, elem):
        """Returns width of rectangle
        """

        giga_size = int(round(elem['size'] / 1000000000.0))
        if giga_size < MIN_WIDTH:
            width = MIN_WIDTH
        elif giga_size > MAX_WIDTH and elem['type'] != 'vg':
            # I don't want too wide disks. VG is ok, cause its width depends on
            # its logical volumes.
            width = MAX_WIDTH
        else:
            width = giga_size
        return width


    def add_left_icons(self, elem, icons, box):
        """Adds appropriate icons to the top left corner of rectangle.
        """
        icon_name = None
        
        cond2 = elem['type'].startswith('raid')
        if elem['type'] in ['disk', 'loop', 'part', 'lv', 'vg', 'pv'] or cond2:
            if elem['label']['type']['short'] == 'Cache pool':
                pass
            elif elem['fstype'].startswith('LVM'):
                icon_name = 'pv'
            elif elem['children']:
                child = get_by_uuid(elem['children'][0], self.all_elems)
                if child['type'] == 'pv':
                    icon_name = 'pv'
                else:
                    pass
            elif elem['mountpoint']:
                icon_name = 'mount'
            elif elem['fstype'] in FS_TYPES:
                icon_name = 'fs'
            else:
                icon_name = 'free'
            
        if icon_name:
            icon = Gtk.Image.new_from_pixbuf(icons[icon_name])        
            box.pack_start(icon, False, False, 0)
            
        if elem['encrypted']:
            icon = Gtk.Image.new_from_pixbuf(icons['crypt'])
            box.pack_start(icon, False, False, 0)
            

    def add_right_icons(self, elem, icons, box):
        """Adds appropriate icons to the top left corner of rectangle.
        """
        
        icon = Gtk.Image.new_from_pixbuf(icons['menu'])
        box.pack_start(icon, False, False, 0)
        
        
    def get_icons(self):
        """Returns dictionary of icons to use in the rectangles.
        """
        
        pixbuf = GdkPixbuf.Pixbuf()
        dict_icons = {}
        dict_icons['free'] = pixbuf.new_from_file_at_size('graphics/free.png', 10, 10)
        dict_icons['pv'] = pixbuf.new_from_file_at_size('graphics/pv.png', 10, 10)
        dict_icons['mount'] = pixbuf.new_from_file_at_size('graphics/mount.png', 10, 10)
        dict_icons['fs'] = pixbuf.new_from_file_at_size('graphics/fs.jpg', 9, 9) 
        dict_icons['crypt'] = pixbuf.new_from_file_at_size('graphics/crypt.png', 10, 12)
        dict_icons['menu'] = pixbuf.new_from_file_at_size('graphics/menu.png', 13, 13)
        return dict_icons
        
    def get_label(self, elem):
        """Returns appropriate label.
        """
        if elem['type'] == 'pv':
            name = elem['name'].split('/')[-1]
        else:
            name = elem['name']
            
        type_label = elem['label']['type']['short']
        markup = '<b>%s</b>\n<small>%s</small>' %(name, type_label)
        label = Gtk.Label(justify=Gtk.Justification.CENTER, max_width_chars=5,                          
                        ellipsize=Pango.EllipsizeMode.END)
        label.set_markup(markup)
        
        return label
    
    
    def get_progress_bar(self, occupied):
        """Returns progress bar that shows amount of the occupied space.
        """
        
        text = '%.0f %% occupied' % occupied
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(occupied/100)
        progress_bar.set_text(text)
        progress_bar.set_show_text(True)
        
        return progress_bar
    

    