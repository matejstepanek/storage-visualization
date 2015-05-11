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
    """
    
    def __init__(self, main_window, all_elements, pvs, vgs, lvs, disks_loops):
        
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                         margin_top=40, margin_bottom=40,
                         margin_left=10, margin_right=10,
                         halign=Gtk.Align.CENTER)
        
        self.V_GAP_SMALL = 4
        self.V_GAP_BIG = 10
        self.H_GAP_SMALL = 4
        self.H_GAP_BIG = 15
        
        self.main_window = main_window
        self.all_elements = all_elements
        
        self.color_pairs = {}
        self.colors = ['Orange', 'Chocolate', 'Chameleon', 'SkyBlue', 'Plum', 'ScarletRed']
        self.color_iterator = 0
        
        self.rectangles = {}
        
        
        physical_area = PhysicalArea(self, all_elements, disks_loops)
        self.pack_start(physical_area, False, False, 0)
         
        separator = Gtk.Separator(margin_top=self.V_GAP_BIG, margin_bottom=self.V_GAP_BIG)
        self.pack_start(separator, False, False, 0)
           
        logical_area = LogicalArea(self, all_elements, pvs, vgs, lvs)
        self.pack_start(logical_area, False, False, 0)
        
        
#         self.connect('button-press-event', self.on_button_press)
        self.show_all()


    def add_rectangle(self, elem, box, expand_fill=False):
        """Adds rectangle to a given box.
        """
        
        self.rectangles[elem['uuid']] = rectangle.Rectangle(elem, self.all_elements,
                                                           self.main_window)
        
        self.rectangles[elem['uuid']].set_name(elem['uuid'])
        
        
        if elem['type'] == 'lv':
            
            if elem['is_origin']:
                self.set_color(elem['name'], self.rectangles[elem['uuid']].color_box)
            
            if elem['origin'] and elem['segtype'] != 'cache':
                self.set_color(elem['origin'], self.rectangles[elem['uuid']].color_box)
        
        
        if expand_fill:
            box.pack_start(self.rectangles[elem['uuid']], True, True, 0)
        else:  
            box.pack_start(self.rectangles[elem['uuid']], False, False, 0)

    
    def set_color(self, elem_name, widget):
        """Sets color of a given widget. (For snapshots and their origins.)
        """
        
        if elem_name in self.color_pairs:
            color = self.color_pairs[elem_name]
            widget.set_name(color)
        else:
            color = self.colors[self.color_iterator]
            self.color_pairs[elem_name] = color
            widget.set_name(color)
            self.color_iterator += 1

            
    def on_button_press(self, widget, event):
        
        print 'scheme'

