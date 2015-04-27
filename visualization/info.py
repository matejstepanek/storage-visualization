'''
Created: 2015

@author: mstepane@redhat.com

Box with information about a selected storage element.
'''

from gi.repository import Gtk #@UnresolvedImport

from data.utils import get_by_uuid


class InfoBox(Gtk.Box):
    """Box with information about a selected storage element.
    """
    
        
    def __init__(self, all_elements, uuid=None):
        
        Gtk.Box.__init__(self, halign=Gtk.Align.CENTER, spacing=5, margin_top=13,
                         margin_left = 10, margin_right = 10)
        
        self.clear()
        
        elem = get_by_uuid(uuid,all_elements)

        if elem:
            
            vbox_keys = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.pack_start(vbox_keys, False, True, 0)

            vbox_values = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.pack_start(vbox_values, False, True, 0)
            
            
            for text in ['Name:','Type:','Size:']:
                self.add_label(text, vbox_keys, 1)

            name = '<b>%s</b>' %elem['label']['name']
            self.add_label(name, vbox_values, 0)
            
            text_type = elem['label']['type']['long']
            if elem['type'] in ['pv','lv']:
                text_type += ' - in volume group %s' %elem['vg_name']
            self.add_label(text_type, vbox_values, 0)
            
            self.add_label(elem['label']['size'], vbox_values)
            
            
            if elem['label']['content']:
                self.add_label('Content:', vbox_keys, 1)
                self.add_label(elem['label']['content'], vbox_values)
            

#             self.add_label('uuid:', vbox_keys, 1)
#             self.add_label(elem['uuid'], vbox_values)
#             
#             self.add_label('Parents:', vbox_keys, 1)
#             self.add_label(str(elem['parents']), vbox_values)
#             
#             self.add_label('Children:', vbox_keys, 1)
#             self.add_label(str(elem['children']), vbox_values)


        self.show_all()


    def add_label(self, text, box, xalign=0):
        """Adds label with a given (markup) string to a given box.
        """
        
        label = Gtk.Label(xalign = xalign)
        label.set_markup(text)
        box.pack_start(label, False, True, 0)
        
        
    def clear(self):
        """Removes previous information shown in info box.
        """
        
        children = self.get_children()
        
        for child in children:
            
            child.destroy()

