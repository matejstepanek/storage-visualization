#!/usr/bin/python
'''
Created: 2014 - 2015

@author: mstepane

Displaying storage layers in GUI.
'''

from gi.repository import Gtk, Gdk, GdkPixbuf, Pango   #@UnresolvedImport
import subprocess
import data

FS_TYPES = ['ext3', 'ext4', 'vfat', 'ntfs', 'btrfs']
MIN_WIDTH = 110
MAX_WIDTH = 500
V_GAP_SMALL = 4
V_GAP_BIG = 10
H_GAP_SMALL = 4
H_GAP_BIG = 15


class Dialog1(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, 'loop3 (Loop device)', parent, 0)

        self.set_default_size(160, 100)

        box = self.get_content_area()

        form = Gtk.Button('Format')
        encrypt = Gtk.Button('Encrypt')
        create = Gtk.Button('Create PV')
        detach = Gtk.Button('Detach')
        box.pack_start(form, True, True, 0)
        box.pack_start(encrypt, True, True, 0)
        box.pack_start(create, True, True, 0)
        box.pack_start(detach, True, True, 0)
        self.show_all()
        
        self.connect('button-press-event', self.on_button_press)
    
    def on_button_press(self, widget, event):
#         print 'aaaaaaaaa'
        self.destroy
 
class Dialog2(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, 'loop3 (Physical volume)', parent, 0)

        self.set_default_size(160, 100)

        box = self.get_content_area()

        add1 = Gtk.Button('Add to VG alpha')
        add2 = Gtk.Button('Add to VG fedora')
        remove = Gtk.Button('Remove')
        box.pack_start(add1, True, True, 0)
        box.pack_start(add2, True, True, 0)
        box.pack_start(remove, True, True, 0)
        self.show_all()
        
        self.connect('button-press-event', self.on_button_press)
    
    def on_button_press(self, widget, event):
#         print 'aaaaaaaaa'
        self.destroy
               
        

class Rectangle(Gtk.Button):
    """Rectangle representing one storage element (disk, volume group, LV, ...)
    """
    __gtype_name__ = 'Rectangle'
    
    def __init__(self, elem, all_elems):
        """Initiates rectangle with appropriate size, icons and label.
        """
        
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
#         elif elem['type'] == 'lv' and (elem['data_percent'] or elem['data_percent']==0.00):
        elif elem['type'] == 'lv' and elem['data_percent'] != '':
            occupied = elem['data_percent']
            progress_bar = self.get_progress_bar(occupied)
            vbox.pack_end(progress_bar, False, False, 0)
        # free space progress bar for mounted file systems
        elif elem['mountpoint']:
            mounted = data.get_mounted()
            mpoint = elem['mountpoint']
            if mpoint in mounted.keys():
                occupied = mounted[elem['mountpoint']]
                progress_bar = self.get_progress_bar(occupied)
                vbox.pack_end(progress_bar, False, False, 0)
            
        self.connect('button-press-event', self.on_button_press)
                
    def menu_press_1(self, widget, event):
        subprocess.check_output(['sudo', 'pvcreate', '/dev/loop3'])
        window.paned.destroy()
        window.__init__()
        
    def menu_press_2(self, widget, event):
        subprocess.check_output(['sudo', 'vgextend', 'alpha', '/dev/loop3'])
        window.paned.destroy()
        window.__init__()
    
    def on_button_press(self, widget, event):

        elem = data.get_by_uuid(self.uuid, self.all_elems)
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
                
#                 print 'akce 1'
#                 dialog = Dialog1(window)
#                 response = dialog.run()
#                 if response:
#                     subprocess.check_output(['sudo', 'pvcreate', '/dev/loop3'])
#                     window.paned.destroy()
#                     window.__init__()
#                     print 'dialog 1 konec'
#                 dialog.destroy()
                
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
                
#                 print 'akce 2'
#                 dialog = Dialog2(window)
#                 response = dialog.run()
#                 if response:
#                     subprocess.check_output(['sudo', 'vgextend', 'alpha', '/dev/loop3'])
#                     window.paned.destroy()
#                     window.__init__()
#                     print 'dialog 2 konec'
#                 dialog.destroy()
                
            elif elem['name'] == 'sda':
                if True:
                    subprocess.check_output(['sudo', 'vgreduce', 'alpha', '/dev/loop3'])
                    subprocess.check_output(['sudo', 'pvremove', '/dev/loop3'])
                    window.paned.destroy()
                    window.__init__()
                    
        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            self.draw_dependencies()
        else:
            rectangle = window.scheme_box.rectangle
            for rec in rectangle.itervalues():
                rec.set_name('Rectangle') 
            window.scheme_box.info_box.box.destroy()
            window.scheme_box.info_box.__init__(self.all_elems, self.uuid)
    
    def draw_dependencies(self):
        rectangle = window.scheme_box.rectangle
        dependencies = self.get_dependencies()
        for uuid in rectangle:
            if uuid in dependencies:
                rectangle[uuid].set_name('Dependency')
            
    def get_dependencies(self):
 
        elem = data.get_by_uuid(self.uuid, self.all_elems)
        dependencies = [self.uuid]
        
        # Appends parents and grandparents and so on.
        for p_uuid in elem['parents']:
            dependencies.append(p_uuid)
            p = data.get_by_uuid(p_uuid,self.all_elems)
            for p1_uuid in p['parents']:
                dependencies.append(p1_uuid)
                p1 = data.get_by_uuid(p1_uuid,self.all_elems)
                for p2_uuid in p1['parents']:
                    dependencies.append(p2_uuid)
                    p2 = data.get_by_uuid(p2_uuid,self.all_elems)
                    for p3_uuid in p2['parents']:
                        dependencies.append(p3_uuid)
                        p3 = data.get_by_uuid(p3_uuid,self.all_elems)
                        for p4_uuid in p3['parents']:
                            dependencies.append(p4_uuid)
                            p4 = data.get_by_uuid(p4_uuid,self.all_elems)
                            for p5_uuid in p4['parents']:
                                dependencies.append(p5_uuid)
                                p5 = data.get_by_uuid(p5_uuid,self.all_elems)
                                for p6_uuid in p5['parents']:
                                    dependencies.append(p6_uuid)
                                    p6 = data.get_by_uuid(p6_uuid,self.all_elems)
                                    for p7_uuid in p6['parents']:
                                        dependencies.append(p7_uuid)
                                        p7 = data.get_by_uuid(p7_uuid,self.all_elems)
                                        for p8_uuid in p7['parents']:
                                            dependencies.append(p8_uuid)
                                            p8 = data.get_by_uuid(p8_uuid,self.all_elems)
                                            for p9_uuid in p8['parents']:
                                                dependencies.append(p9_uuid)
                                                p9 = data.get_by_uuid(p9_uuid,self.all_elems)
                                                for p10_uuid in p9['parents']:
                                                    dependencies.append(p10_uuid)
        # Appends children, grandchildren and so on.
        for p_uuid in elem['children']:
            dependencies.append(p_uuid)
            p = data.get_by_uuid(p_uuid,self.all_elems)
            for p1_uuid in p['children']:
                dependencies.append(p1_uuid)
                p1 = data.get_by_uuid(p1_uuid,self.all_elems)
                for p2_uuid in p1['children']:
                    dependencies.append(p2_uuid)
                    p2 = data.get_by_uuid(p2_uuid,self.all_elems)
                    for p3_uuid in p2['children']:
                        dependencies.append(p3_uuid)
                        p3 = data.get_by_uuid(p3_uuid,self.all_elems)
                        for p4_uuid in p3['children']:
                            dependencies.append(p4_uuid)
                            p4 = data.get_by_uuid(p4_uuid,self.all_elems)
                            for p5_uuid in p4['children']:
                                dependencies.append(p5_uuid)
                                p5 = data.get_by_uuid(p5_uuid,self.all_elems)
                                for p6_uuid in p5['children']:
                                    dependencies.append(p6_uuid)
                                    p6 = data.get_by_uuid(p6_uuid,self.all_elems)
                                    for p7_uuid in p6['children']:
                                        dependencies.append(p7_uuid)
                                        p7 = data.get_by_uuid(p7_uuid,self.all_elems)
                                        for p8_uuid in p7['children']:
                                            dependencies.append(p8_uuid)
                                            p8 = data.get_by_uuid(p8_uuid,self.all_elems)
                                            for p9_uuid in p8['children']:
                                                dependencies.append(p9_uuid)
                                                p9 = data.get_by_uuid(p9_uuid,self.all_elems)
                                                for p10_uuid in p9['children']:
                                                    dependencies.append(p10_uuid)
        
        return dependencies
    
    def get_width(self, elem):
        """Returns width of rectangle
        """
#         if elem['type'].startswith('raid'):
#             for uuid in elem['parents']:
#                 a = window.scheme_box.rectangle[uuid]
        
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
                child = data.get_by_uuid(elem['children'][0], self.all_elems)
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
#         button = Gtk.Button()
#         button.add(icon)
        box.pack_start(icon, False, False, 0)
        
    def get_icons(self):
        """Returns dictionary of icons to use in the rectangles.
        """
        pixbuf = GdkPixbuf.Pixbuf()
        dict_icons = {}
        dict_icons['free'] = pixbuf.new_from_file_at_size('../graphics/free.png', 10, 10)
        dict_icons['pv'] = pixbuf.new_from_file_at_size('../graphics/pv.png', 10, 10)
        dict_icons['mount'] = pixbuf.new_from_file_at_size('../graphics/mount.png', 10, 10)
        dict_icons['fs'] = pixbuf.new_from_file_at_size('../graphics/fs.jpg', 9, 9) 
        dict_icons['crypt'] = pixbuf.new_from_file_at_size('../graphics/crypt.png', 10, 12)
        dict_icons['menu'] = pixbuf.new_from_file_at_size('../graphics/menu.png', 13, 13)
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
    
             
class Scheme(Gtk.Box):
    """Scheme of storage layers with information box.
    
    Structure of scheme:
    - layers
        - disks_partitions_area hbox
            - disk_box vbox
                - disk rectangles
                - part_rows hbox
                    - partition rectangles
        - separator1
        (- mdraids_row)    
        (- separator2)
        - lvm_area
            - vg_boxes_plus vbox
                - vg_alignment
                    - vg_boxes vbox
                        - pv_rows hbox
                            - pv rectangles
                        - vg rectangles
                        - lv_rows hbox
                            - lv rectangles
                - thin_rows hbox
                    - frame
                        - thin_box hbox
                            - thin lv rectangles
            - vg_boxes['@no vg'] vbox
                - pv_rows['@no vg'] hbox
                    - pv rectangles
    """
    
    def __init__(self, all_elems, pvs, vgs, lvs, disks_loops):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                          width_request=200)
        
        self.all_elems = all_elems
        
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(self.box, True, True, 0)
        
        scrolled_window_main = Gtk.ScrolledWindow()
        scrolled_window_main.set_name('White')
        self.box.pack_start(scrolled_window_main, True, True, 0)
       
        layers = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                         halign=Gtk.Align.CENTER,
                         margin_top=40, margin_bottom=40,
                         margin_left=10, margin_right=10)
        scrolled_window_main.add(layers)
        
        self.rectangle = {}
        
        ########## DISKS, PARTITIONS AND MD RAID AREA ##########################
        disks_partitions_area = Gtk.Box(halign=Gtk.Align.CENTER,
                                        spacing=H_GAP_BIG)
        layers.add(disks_partitions_area)
        
        separator1 = Gtk.Separator(margin_top=V_GAP_BIG, margin_bottom=V_GAP_BIG)
        layers.add(separator1)
        
        md_raid_present = False
        md_raids_added = []
        
        # disks, partitions and md raid rectangles
        for disk in disks_loops:
            disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                               spacing=V_GAP_SMALL)
            disks_partitions_area.add(disk_box)
            
            self.add_rectangle(disk, disk_box)
            
            part_rows = Gtk.Box(spacing=H_GAP_SMALL)
            disk_box.add(part_rows)
            
            for elem_uuid in disk['children']:
                elem = data.get_by_uuid(elem_uuid, all_elems)
                if elem['type'] == 'pv':
                    break
                elif elem['type'] == 'part':
                    self.add_rectangle(elem, part_rows)
                else:
                    # md raids 
                    if not md_raid_present:  
                        mdraids_row = Gtk.Box(halign=Gtk.Align.CENTER,
                                              spacing=H_GAP_BIG)
                        layers.add(mdraids_row)
                        md_raid_present = True 
                        
                    if elem['uuid'] not in md_raids_added:             
                        self.add_rectangle(elem, mdraids_row)
                        md_raids_added.append(elem['uuid'])
                # md raids        
                for elem2_uuid in elem['children']:
                    elem2 = data.get_by_uuid(elem2_uuid, all_elems)
                    if elem2['type'] == 'pv':
                        break
                    elif not md_raid_present:  
                        mdraids_row = Gtk.Box(halign=Gtk.Align.CENTER,
                                              spacing=H_GAP_BIG)
                        layers.add(mdraids_row)
                        md_raid_present = True   
                                   
                    if elem2['uuid'] not in md_raids_added:             
                        self.add_rectangle(elem2, mdraids_row)
                        md_raids_added.append(elem2['uuid'])
                    
        if md_raid_present:
            separator2 = Gtk.Separator(margin_top=V_GAP_BIG,
                                       margin_bottom=V_GAP_BIG)
            layers.add(separator2)
                        
        #################### LVM AREA ##########################################        
        lvm_area = Gtk.Box(halign=Gtk.Align.CENTER, spacing=H_GAP_BIG)
        layers.add(lvm_area)          
         
        vg_boxes_plus = {}
        vg_alingment = {}
        vg_boxes = {} 
        pv_rows = {}
        lv_rows = {}
        thin_rows = {}
        cached = {}
        
        # volume groups rectangles
        for vg in vgs:
            vg_name = vg['name']
            vg_boxes_plus[vg_name] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            lvm_area.add(vg_boxes_plus[vg_name])
            
            vg_alingment[vg_name] = Gtk.Alignment(xalign=0.5)
            vg_boxes_plus[vg_name].add(vg_alingment[vg_name])
            
            vg_boxes[vg_name] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                        halign=Gtk.Align.CENTER,
                                        spacing=V_GAP_SMALL)
            vg_alingment[vg_name].add(vg_boxes[vg_name])
            
            pv_rows[vg_name] = Gtk.Box(spacing=H_GAP_SMALL)
            vg_boxes[vg_name].add(pv_rows[vg_name])
            
            self.add_rectangle(vg, vg_boxes[vg_name])
            
            lv_rows[vg_name] = Gtk.Box(spacing=H_GAP_SMALL)
            vg_boxes[vg_name].add(lv_rows[vg_name])  
            
            thin_rows[vg_name] = Gtk.Box(spacing=H_GAP_SMALL)                      
            
            thin_pools = []
            rest = []
            # cache logical volumes rectangles
            for lv_uuid in vg['children']:                
                lv = data.get_by_uuid(lv_uuid, lvs)   
                if lv['segtype'] == 'cache-pool':
                    continue
                elif lv['segtype'] == 'cache':
                    lv_name = lv['name']
                    cached[lv_name] = Gtk.Box()
                    lv_rows[vg_name].add(cached[lv_name])
                    
                    cache_pool = data.get_by_name(lv['pool_lv'], lvs)
                    self.add_rectangle(cache_pool, cached[lv_name])
                    
                    pixbuf = GdkPixbuf.Pixbuf()
                    arrow = pixbuf.new_from_file_at_size('../graphics/cache.png', 10, 20)
                    icon = Gtk.Image.new_from_pixbuf(arrow)

                    cached[lv_name].add(icon)
                    
                    self.add_rectangle(lv, cached[lv_name])
      
                elif lv['label']['type']['long'].startswith('Thin pool'):
                    thin_pools.append(lv_uuid)
                    continue
                else:
                    rest.append(lv_uuid)

            # thin pools   
            for pool_uuid in thin_pools:
                pool = data.get_by_uuid(pool_uuid, lvs)                
                self.add_rectangle(pool, lv_rows[vg_name])                 
                
                if pool['children']:            
                    frame = Gtk.Frame(label=pool['name'])                    
                    thin_rows[vg_name].add(frame)
                    
                    thin_box = Gtk.Box(margin_left=3, margin_right=3,
                                       margin_bottom=3, spacing=H_GAP_SMALL)
                    frame.add(thin_box)
                    
                # thin logical volumes rectangles                
                for thin_lv_uuid in pool['children']:
                    thin_lv = data.get_by_uuid(thin_lv_uuid, lvs)
                    self.add_rectangle(thin_lv, thin_box)    
                                
            vg_boxes_plus[vg_name].add(thin_rows[vg_name])
            
            # logical volumes rectangles
            for lv_uuid in rest:
                lv = data.get_by_uuid(lv_uuid, lvs)   
                self.add_rectangle(lv, lv_rows[vg_name])      
     

        # physical volumes not used in any VG
        vg_boxes['@no vg'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lvm_area.add(vg_boxes['@no vg'])
        pv_rows['@no vg'] = Gtk.Box(spacing=H_GAP_BIG)
        vg_boxes['@no vg'].add(pv_rows['@no vg']) 
               
        # physical volumes rectangles
        for pv in pvs:
            vg_name = pv['vg_name']
            if vg_name:
                self.add_rectangle(pv, pv_rows[vg_name], True)
            else:
                self.add_rectangle(pv, pv_rows['@no vg'])
                
        ################ INFO BOX ##############################################                                    
        scrolled_window_info = Gtk.ScrolledWindow(height_request=90,
                                    vscrollbar_policy=Gtk.PolicyType.NEVER)
        self.box.pack_start(scrolled_window_info, False, False, 0)
        
        self.info_box = InfoBox(all_elems)
        scrolled_window_info.add(self.info_box)
        self.show_all()
    
    def add_rectangle(self, elem, box, expand_fill=False):
        """Adds rectangle to given box.
        """
        self.rectangle[elem['uuid']] = Rectangle(elem, self.all_elems)
        
        self.rectangle[elem['uuid']].set_name(elem['uuid'])
        
        if elem['type'] == 'lv':
            if elem['is_origin']:
                self.set_color(elem['name'], self.rectangle[elem['uuid']].color_box)
            if elem['origin'] and elem['segtype'] != 'cache':
                self.set_color(elem['origin'], self.rectangle[elem['uuid']].color_box)
        
        if expand_fill:
            box.pack_start(self.rectangle[elem['uuid']], True, True, 0)
        else:  
            box.pack_start(self.rectangle[elem['uuid']], False, False, 0)

    color_pairs = {}
    colors = ['Orange', 'Chocolate', 'Chameleon', 'SkyBlue', 'Plum', 'ScarletRed']
    color_iterator = 0

    def set_color(self, elem_name, widget):
        """Sets color of given rectangle. (For snapshots and their origins.)
        """
        if elem_name in self.color_pairs:
            color = self.color_pairs[elem_name]
            widget.set_name(color)                   
        else:
            color = self.colors[self.color_iterator]
            self.color_pairs[elem_name] = color
            widget.set_name(color)
            self.color_iterator += 1
    
    
class InfoBox(Gtk.Alignment):
    
    __gtype_name__ = 'InfoBox'    
    
    def __init__(self, all_elems, uuid=None):
        Gtk.Alignment.__init__(self, xalign=0.5)
        
        elem = data.get_by_uuid(uuid,all_elems)
        
        self.box = Gtk.Box(halign=Gtk.Align.CENTER, spacing=5, margin_top=15)
        self.add(self.box)
          
        if elem:      
            vbox_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            vbox_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            
            self.box.pack_start(vbox_left, False, True, 0)
            self.box.pack_start(vbox_right, False, True, 0)
            
            for text in ['Name:','Type:','Size:']:
                label = Gtk.Label(text, xalign=1)
                vbox_left.pack_start(label, False, True, 0)

            markup = '<b>%s</b>' %elem['label']['name']
            label = Gtk.Label(xalign=0)
            label.set_markup(markup)
            
            vbox_right.pack_start(label, False, True, 0)
            label = Gtk.Label(elem['label']['type']['long'], xalign=0)
            vbox_right.pack_start(label, False, True, 0)
            label = Gtk.Label(elem['label']['size'], xalign=0)
            vbox_right.pack_start(label, False, True, 0)
            
            if elem['label']['content']:
                label = Gtk.Label('Content:', xalign=1)
                vbox_left.pack_start(label, False, True, 0)
                label = Gtk.Label(elem['label']['content'], xalign=0)
                vbox_right.pack_start(label, False, True, 0)
            
            if elem['type'] in ['pv','lv']:
                label = Gtk.Label('VG name:', xalign=1)
                vbox_left.pack_start(label, False, True, 0)
                label = Gtk.Label(elem['vg_name'], xalign=0)
                vbox_right.pack_start(label, False, True, 0)
                
#             label = Gtk.Label('uuid:', xalign=1)
#             vbox_left.pack_start(label, False, True, 0)
#             label = Gtk.Label(elem['uuid'], xalign=0)
#             vbox_right.pack_start(label, False, True, 0)
#             
#             label = Gtk.Label('Parents:', xalign=1)
#             vbox_left.pack_start(label, False, True, 0)
#             label = Gtk.Label(elem['parents'], xalign=0)
#             vbox_right.pack_start(label, False, True, 0)
#                
#             label = Gtk.Label('Children:', xalign=1)
#             vbox_left.pack_start(label, False, True, 0)
#             label = Gtk.Label(elem['children'], xalign=0)
#             vbox_right.pack_start(label, False, True, 0)

        self.show_all()
        
        
class TreeView(Gtk.TreeView): 
    
    def __init__(self, tree_store, all_elems):
        self.all_elems = all_elems
        
        Gtk.TreeView.__init__(self, tree_store)
        self.connect('row_activated', self.on_row_activated)
        self.set_activate_on_single_click(True)
        
    def on_row_activated(self, widget, path, column):
        tree_store = self.get_model()
        it = tree_store.get_iter(path)
        elem_id = tree_store.get_value(it,2)
        
        window.scheme_box.info_box.box.destroy()
        window.scheme_box.info_box.__init__(self.all_elems, elem_id)
        
        window.scheme_box.rectangle[elem_id].emit('focus', False)
        
class TreePanel(Gtk.Box): 
    """Panel with tree structure of block devices and logical volumes.
    """      
    
    def __init__(self, all_elems, vgs, lvs, disks_loops):
        
        self.all_elems = all_elems
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                          width_request=200)                                      
        # Disk tree        
        store_disks = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_disks, all_elems, disks_loops, 'name')
        view_disks = TreeView(store_disks, all_elems)
        view_disks.set_headers_visible(False)
#         view_disks.expand_all()
        view_disks.set_enable_tree_lines(True)
        
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        view_disks.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Disks', renderer_text, text=1)
        view_disks.append_column(column_text)
              
        scrolled_window_view_disks = Gtk.ScrolledWindow()
        scrolled_window_view_disks.add(view_disks)
        
        # VG tree
        store_vgs = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_vgs, all_elems, vgs, 'name')
        view_vgs = TreeView(store_vgs, all_elems)
        view_vgs.set_headers_visible(False)
#         view_vgs.expand_all()
        view_vgs.set_enable_tree_lines(True)
                
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        view_vgs.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Volume groups', renderer_text, text=1)        
        view_vgs.append_column(column_text)
        
        scrolled_window_view_vgs = Gtk.ScrolledWindow()
        scrolled_window_view_vgs.add(view_vgs)
        
        # mountpoints tree
        mpoints = []
        for elem in all_elems:
            if elem['mountpoint']:
                mpoints.append(elem)
        
        store_mountpoints = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        self.populate_store(store_mountpoints, all_elems, mpoints, 'mountpoint')
        view_mountpoints = TreeView(store_mountpoints, all_elems)
        view_mountpoints.set_headers_visible(False)
#         view_mountpoints.expand_all()
        view_mountpoints.set_enable_tree_lines(True)
                
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        view_mountpoints.append_column(column_pixbuf)
        
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn('Mount points', renderer_text, text=1)        
        view_mountpoints.append_column(column_text)
        
        scrolled_window_view_mountpoints = Gtk.ScrolledWindow()
        scrolled_window_view_mountpoints.add(view_mountpoints)
        
        # Sets the stack and his switcher.
        stack = Gtk.Stack()
        
        stack.add_titled(scrolled_window_view_disks, 'disks', 'Disks')        
        stack.add_titled(scrolled_window_view_vgs, 'vgs', 'Volume groups')
        stack.add_titled(scrolled_window_view_mountpoints, 'mountpoints', 'Mount points')

        
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        
        self.pack_start(stack_switcher, False, True, 0)
        self.pack_start(stack, True, True, 0)
      
    def populate_store(self, store, elements, roots, info):
        """Populates tree store with data.
        
        Roots are added at first. And then 2 more layers. That is enough
        for disk trees and vgs trees both.
        """
        for elem1 in roots:            
            parent_row2 = self.append_row(elem1, store, None, info)                        
            for elem2_uuid in elem1['children']:              
                elem2 = data.get_by_uuid(elem2_uuid, elements)
                if elem2['type'] == 'pv':
                    break  
                parent_row3 = self.append_row(elem2, store, parent_row2, info)                                                  
                for elem3_uuid in elem2['children']:
                    elem3 = data.get_by_uuid(elem3_uuid, elements)
                    if elem3['type'] == 'pv':
                        break 
                    parent_row4 = self.append_row(elem3, store, parent_row3, info)                        
                    for elem4_uuid in elem3['children']:
                        elem4 = data.get_by_uuid(elem4_uuid, elements)
                        if elem4['type'] == 'pv':
                            break
                        self.append_row(elem4, store, parent_row4, info)  
                        
    def append_row(self, elem, store, parent_row, info): 
        """Appends row with given element.
        """        
        icon = self.assign_icon(elem)
        text = elem[info]
        new_parent_row = store.append(parent_row,[icon, text, elem['uuid']])
        return new_parent_row
    
    def assign_icon(self, elem):
        """Returns appropriate icon for element to display in the tree view.
        """
        icons = self.get_icons()
        icon = icons['free']        
        if elem['label']['type']['short'] == 'Cache pool':
                icon = None
        elif elem['children']:
            child = data.get_by_uuid(elem['children'][0], self.all_elems)
            if child['type'] == 'pv':
                icon = icons['pv'] 
            else:
                icon = None
        if elem['mountpoint']:
            icon = icons['mount']
        elif elem['fstype'] in FS_TYPES:
            icon = icons['fs']
        if elem['fstype'].startswith('LVM'):
            icon = icons['pv']       
        return icon
    
    def get_icons(self):
        """Returns dictionary of icons to use in the tree view.
        """
        pixbuf = GdkPixbuf.Pixbuf()
        dict_icons = {}
        dict_icons['free'] = pixbuf.new_from_file_at_size('../graphics/free.png', 10, 10)
        dict_icons['pv'] = pixbuf.new_from_file_at_size('../graphics/pv.png', 10, 10)
        dict_icons['mount'] = pixbuf.new_from_file_at_size('../graphics/mount.png', 10, 10)
        dict_icons['fs'] = pixbuf.new_from_file_at_size('../graphics/fs.jpg', 9, 9)
        return dict_icons
    

class MainWindow(Gtk.Window):
    """Window with whole GUI.
    """     
    def __init__(self): 
        """Draws a GUI and displays storage scheme and tree panel in it.
        """       
        Gtk.Window.__init__(self, default_width=1400, default_height=700, 
                            width_request=400, height_request=500,
                            border_width=5, title='Storage visualization')

        elems = data.Elements()
        (all_elems, pvs, vgs, lvs, disks_loops) = elems.get_data()
              
        self.paned = Gtk.Paned()
        self.add(self.paned)
    
        self.scheme_box = Scheme(all_elems, pvs, vgs, lvs, disks_loops)
        self.paned.pack1(self.scheme_box, True, False)        

        tree_panel = TreePanel(all_elems, vgs, lvs, disks_loops)
        self.paned.pack2(tree_panel, False, True)
        
        self.show_all()     

######################### Set css style of GUI #################################
screen = Gdk.Screen.get_default()

css_provider = Gtk.CssProvider()
css_provider.load_from_path('styles.css')

context = Gtk.StyleContext()
context.add_provider_for_screen(screen, css_provider,
                                Gtk.STYLE_PROVIDER_PRIORITY_USER)
################################################################################

window = MainWindow()
window.connect('delete-event', Gtk.main_quit)
window.show_all()
Gtk.main()