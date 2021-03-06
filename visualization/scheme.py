'''
Created: 2015

@author: mstepane@redhat.com

Scheme of storage layers.
'''

from gi.repository import Gtk #@UnresolvedImport

from physical_area import PhysicalArea
from logical_area import LogicalArea
import rectangle


class SchemeBox(Gtk.Box):
    """Scheme of storage layers.
    
    Physical area:
        1. disks
        2. partitions
    -----------------------------
        3. md raids
    -----------------------------
    Logical area:
        1. physical volumes
        2. volume groups
        3. logical volumes, thin pools
        4. thin logical volumes
    """
    
    def __init__(self, main_window):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                         margin_top=40, margin_bottom=30,
                         margin_left=30, margin_right=30)
        
        self.main_window = main_window
        
        self.V_GAP_SMALL = 4
        self.V_GAP_BIG = 10
        self.H_GAP_SMALL = 4
        self.H_GAP_BIG = 15
        
        self.color_pairs = {}
        self.colors = ['Orange', 'Chocolate', 'Chameleon', 'SkyBlue', 'Plum',
                       'ScarletRed']
        self.color_iterator = 0
        
        self.rectangles = {}
        
        
        physical_area = PhysicalArea(self, main_window)
        self.pack_start(physical_area, False, False, 0)
         
        separator = Gtk.Separator(margin_top=self.V_GAP_BIG,
                                  margin_bottom=self.V_GAP_BIG)
        self.pack_start(separator, False, False, 0)
        
        ordered_pvs = physical_area.ordered_pvs
        logical_area = LogicalArea(self, main_window, ordered_pvs)
        self.pack_start(logical_area, False, False, 0)
        

        self.show_all()


    def add_rectangle(self, element, box, expand_fill=False):
        """Adds rectangle to a given box.
        """
        
        uuid = element['uuid']

        self.rectangles[uuid] = rectangle.Rectangle(element, self.main_window)
        
        self.rectangles[uuid].set_name(uuid)
        
        
        if element['type'] == 'lv':
            
            if element['is_origin']:
                self.set_color(element['name'], self.rectangles[uuid].color_box)
            
            if element['origin'] and element['segtype'] != 'cache':
                self.set_color(element['origin'], self.rectangles[uuid].color_box)
        
        
        if expand_fill:
            box.pack_start(self.rectangles[uuid], True, True, 0)
        else:  
            box.pack_start(self.rectangles[uuid], False, False, 0)

    
    def set_color(self, element_name, widget):
        """Sets color of a given widget. (For snapshots and their origins.)
        
        Rectangles representing snaphots and their origins are tagged with
        the strip of the same color.
        """
        
        if element_name in self.color_pairs:
            color = self.color_pairs[element_name]
            widget.set_name(color)
        else:
            color = self.colors[self.color_iterator]
            self.color_pairs[element_name] = color
            widget.set_name(color)
            self.color_iterator += 1

