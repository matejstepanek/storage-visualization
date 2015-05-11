'''
Created: 2015

@author: mstepane@redhat.com

Area with lvm elements: physical volumes, volume groups, logical volumes.
'''

from gi.repository import Gtk, GdkPixbuf   #@UnresolvedImport

from data.utils import get_by_uuid, get_by_name


class LogicalArea(Gtk.Box):
    """Area with lvm elements: physical volumes, volume groups, logical volumes.
    """
    
    def __init__(self, scheme, all_elements, pvs, vgs, lvs):
        
        Gtk.Box.__init__(self, halign=Gtk.Align.CENTER, spacing=scheme.H_GAP_BIG)
        
        vg_boxes_plus = {}
        vg_alingment = {}
        vg_boxes = {} 
        pv_rows = {}
        self.lv_rows = {}
        thin_rows = {}
        self.cached = {}
        

        for vg in vgs:
            
            vg_name = vg['name']
            
            vg_boxes_plus[vg_name] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.add(vg_boxes_plus[vg_name])
            
            vg_alingment[vg_name] = Gtk.Alignment(xalign=0.5)
            vg_boxes_plus[vg_name].add(vg_alingment[vg_name])
            
            vg_boxes[vg_name] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                        halign=Gtk.Align.CENTER,
                                        spacing=scheme.V_GAP_SMALL)
            vg_alingment[vg_name].add(vg_boxes[vg_name])
            
            pv_rows[vg_name] = Gtk.Box(spacing=scheme.H_GAP_SMALL)
            vg_boxes[vg_name].add(pv_rows[vg_name])
            
            scheme.add_rectangle(vg, vg_boxes[vg_name])
            
            self.lv_rows[vg_name] = Gtk.Box(spacing=scheme.H_GAP_SMALL)
            vg_boxes[vg_name].add(self.lv_rows[vg_name])  
            
            thin_rows[vg_name] = Gtk.Box(spacing=scheme.H_GAP_SMALL)                      
            vg_boxes_plus[vg_name].add(thin_rows[vg_name])
            
            thin_pools = []
            rest = []
           
            for lv_uuid in vg['children']:
                               
                lv = get_by_uuid(lv_uuid, lvs)
                
                if lv:
                    if lv['segtype'] == 'cache-pool':
                        continue
                    
                    elif lv['segtype'] == 'cache':
                        self.add_cache(lv, lvs, vg_name, scheme)
                        
                    elif lv['label']['type']['short'].startswith('Thin pool'):
                        thin_pools.append(lv_uuid)
                        continue
                    
                    else:
                        rest.append(lv_uuid)


            # thin pools   
            for pool_uuid in thin_pools:
                
                pool = get_by_uuid(pool_uuid, lvs)
                
                if pool:               
                    scheme.add_rectangle(pool, self.lv_rows[vg_name])                 
                    
                    if pool['children']:            
                        frame = Gtk.Frame(label=pool['name'])                    
                        thin_rows[vg_name].add(frame)
                        
                        thin_box = Gtk.Box(margin_left=3, margin_right=3,
                                           margin_bottom=3, spacing=scheme.H_GAP_SMALL)
                        frame.add(thin_box)
                    
                # thin logical volumes rectangles                
                for thin_lv_uuid in pool['children']:
                    
                    thin_lv = get_by_uuid(thin_lv_uuid, lvs)
                    
                    if thin_lv:
                        scheme.add_rectangle(thin_lv, thin_box)    
                                
            
            # logical volumes rectangles
            for lv_uuid in rest:
                
                lv = get_by_uuid(lv_uuid, lvs)
                
                if lv: 
                    scheme.add_rectangle(lv, self.lv_rows[vg_name])      
     

        # physical volumes not used in any VG
        vg_boxes['@no vg'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vg_boxes['@no vg'])
        
        pv_rows['@no vg'] = Gtk.Box(spacing=scheme.H_GAP_BIG)
        vg_boxes['@no vg'].add(pv_rows['@no vg']) 
        
               
        # physical volumes rectangles
        for pv in pvs:
            
            vg_name = pv['vg_name']
            
            if vg_name:
                scheme.add_rectangle(pv, pv_rows[vg_name], True)
            else:
                scheme.add_rectangle(pv, pv_rows['@no vg'])
                
    
    def add_cache(self, lv, lvs, vg_name, scheme):
        """Adds a logical volume with lvm cache.
        """
        
        lv_name = lv['name']
        self.cached[lv_name] = Gtk.Box()
        self.lv_rows[vg_name].add(self.cached[lv_name])
        
        cache_pool = get_by_name(lv['pool_lv'], lvs)
        if cache_pool:
            scheme.add_rectangle(cache_pool, self.cached[lv_name])
        
        pixbuf = GdkPixbuf.Pixbuf()
        arrow = pixbuf.new_from_file_at_size('graphics/cache.png', 10, 20)
        icon = Gtk.Image.new_from_pixbuf(arrow)

        self.cached[lv_name].add(icon)
        
        scheme.add_rectangle(lv, self.cached[lv_name])
                    
                    
                    