'''
Created: 2015

@author: mstepane@redhat.com

Area with lvm elements: physical volumes, volume groups, logical volumes.
'''

from gi.repository import Gtk   #@UnresolvedImport

from data.utils import get_by_uuid


class LogicalArea(Gtk.Box):
    """Area with lvm elements: physical volumes, volume groups, logical volumes.
    
    Volume groups are ordered according to disks. (VG on the most left disk
    is the most left.)
    """
    
    def __init__(self, scheme, main_window, ordered_pvs):
        
        Gtk.Box.__init__(self, spacing=scheme.H_GAP_BIG)
        
        
        pvs = main_window.pvs
        vgs = main_window.vgs
        lvs = main_window.lvs
        
        
        vg_boxes_plus = {}
        vg_alingment = {}
        vg_boxes = {} 
        pv_rows = {}
        self.lv_rows = {}
        thin_rows = {}
        
        
        ordered_vgs = self.get_ordered_vgs(ordered_pvs, vgs)
        
        for vg_uuid in ordered_vgs:
            
            vg = get_by_uuid(vg_uuid, vgs)
            
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
            normal_lvs = []
            
           
            for lv_uuid in vg['children']:
                               
                lv = get_by_uuid(lv_uuid, lvs)
                
                if lv:
                        
                    if lv['label']['type']['short'].startswith('Thin pool'):
                        thin_pools.append(lv_uuid)
                    
                    else:
                        normal_lvs.append(lv_uuid)
            
            
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
            for lv_uuid in normal_lvs:
                
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


    def get_ordered_vgs(self, ordered_pvs, vgs):
        """Given ordered pvs returns ordered vgs.
        
        First pv in the list is on the most left disk in the scheme. We want
        volume groups to be in the same order. That means vg on the most left
        disk is added first.
        """
        
        ordered_vgs = []
        
        for pv in ordered_pvs:
            
            if pv['children']:
                vg_uuid = pv['children'][0]
                
                if vg_uuid not in ordered_vgs:
                    ordered_vgs.append(vg_uuid)
        
        return ordered_vgs


        