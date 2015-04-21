'''
Created: 2015

@author: mstepane@redhat.com

Box with information about a selected storage element.
'''

from gi.repository import Gtk #@UnresolvedImport

from data.utils import get_by_uuid


class InfoBox(Gtk.Alignment):
    
#     __gtype_name__ = 'InfoBox'    
    
    def __init__(self, all_elems, uuid=None):
        
        Gtk.Alignment.__init__(self, xalign=0.5)
        
        elem = get_by_uuid(uuid,all_elems)
        
        self.box = Gtk.Box(halign=Gtk.Align.CENTER, spacing=5, margin_top=13)
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
            
            
            text_type = elem['label']['type']['long']
            if elem['type'] in ['pv','lv']:
                text_type += ' - in volume group %s' %elem['vg_name']
            
            label = Gtk.Label(text_type, xalign=0)
            vbox_right.pack_start(label, False, True, 0)
            label = Gtk.Label(elem['label']['size'], xalign=0)
            vbox_right.pack_start(label, False, True, 0)
            
            if elem['label']['content']:
                label = Gtk.Label('Content:', xalign=1)
                vbox_left.pack_start(label, False, True, 0)
                label = Gtk.Label(elem['label']['content'], xalign=0)
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
        

        