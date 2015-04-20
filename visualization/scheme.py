'''
Created: 2015

@author: mstepane@redhat.com

Scheme of storage layers.
'''

from gi.repository import Gtk, GdkPixbuf #@UnresolvedImport

from data.utils import get_by_uuid, get_by_name
import rectangle
import info_box

MIN_WIDTH = 110
MAX_WIDTH = 500
V_GAP_SMALL = 4
V_GAP_BIG = 10
H_GAP_SMALL = 4
H_GAP_BIG = 15


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
    
    def __init__(self, window, all_elems, pvs, vgs, lvs, disks_loops):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                          width_request=200)
        
        self.window = window
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
                elem = get_by_uuid(elem_uuid, all_elems)
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
                    elem2 = get_by_uuid(elem2_uuid, all_elems)
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
                lv = get_by_uuid(lv_uuid, lvs)  
                if lv['segtype'] == 'cache-pool':
                    continue
                elif lv['segtype'] == 'cache':
                    lv_name = lv['name']
                    cached[lv_name] = Gtk.Box()
                    lv_rows[vg_name].add(cached[lv_name])
                    
                    cache_pool = get_by_name(lv['pool_lv'], lvs)
                    self.add_rectangle(cache_pool, cached[lv_name])
                    
                    pixbuf = GdkPixbuf.Pixbuf()
                    arrow = pixbuf.new_from_file_at_size('graphics/cache.png', 10, 20)
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
                pool = get_by_uuid(pool_uuid, lvs)                
                self.add_rectangle(pool, lv_rows[vg_name])                 
                
                if pool['children']:            
                    frame = Gtk.Frame(label=pool['name'])                    
                    thin_rows[vg_name].add(frame)
                    
                    thin_box = Gtk.Box(margin_left=3, margin_right=3,
                                       margin_bottom=3, spacing=H_GAP_SMALL)
                    frame.add(thin_box)
                    
                # thin logical volumes rectangles                
                for thin_lv_uuid in pool['children']:
                    thin_lv = get_by_uuid(thin_lv_uuid, lvs)
                    self.add_rectangle(thin_lv, thin_box)    
                                
            vg_boxes_plus[vg_name].add(thin_rows[vg_name])
            
            # logical volumes rectangles
            for lv_uuid in rest:
                lv = get_by_uuid(lv_uuid, lvs)   
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
        
        self.info_box = info_box.InfoBox(all_elems)
        scrolled_window_info.add(self.info_box)
        self.show_all()


    def add_rectangle(self, elem, box, expand_fill=False):
        """Adds rectangle to given box.
        """
        self.rectangle[elem['uuid']] = rectangle.Rectangle(elem, self.all_elems, self.window)
        
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


