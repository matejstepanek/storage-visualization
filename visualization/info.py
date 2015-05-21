'''
Created: 2015

@author: mstepane@redhat.com

Box with information about the selected storage element.
'''

from gi.repository import Gtk #@UnresolvedImport

from data.utils import get_by_uuid
import visualization.actions as actions


class InfoBox(Gtk.Box):
    """Box with information about the selected storage element.
    """
    

    def __init__(self, all_elements, uuid=None):
        
        Gtk.Box.__init__(self, halign=Gtk.Align.CENTER, height_request=90,
                         spacing=5, margin_top=10,
                         margin_left=10, margin_right=10)
        
        actions.destroy_children(self)
        
        
        element = get_by_uuid(uuid, all_elements)

        if element:
            
            vbox_keys = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.pack_start(vbox_keys, False, True, 0)

            vbox_values = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.pack_start(vbox_values, False, True, 0)
            
            
            for text in ['Name:', 'Type:', 'Size:', 'Content:']:
                self.add_label(text, vbox_keys, 1)


            name = '<b>%s</b>' %element['label']['name']
            self.add_label(name, vbox_values, 0)
            
            
            text_type = element['label']['type']['long']
            
            if element['type'] in ['pv', 'lv'] and element['vg_name']:
                text_type += ' - in volume group %s' %element['vg_name']
                
            self.add_label(text_type, vbox_values, 0)
            
            
            self.add_label(element['label']['size'], vbox_values)
            
            
            self.add_label(element['label']['content'], vbox_values)
            

#             # Uncomment to show more information about a storage element
#             # (uuid, parents, children)
# 
#             self.add_label('uuid:', vbox_keys, 1)
#             self.add_label(element['uuid'], vbox_values)
#              
#             self.add_label('Parents:', vbox_keys, 1)
#             self.add_label(str(element['parents']), vbox_values)
#              
#             self.add_label('Children:', vbox_keys, 1)
#             self.add_label(str(element['children']), vbox_values)


        self.show_all()


    def add_label(self, text, box, xalign=0):
        """Adds label with a given (markup) string to a given box.
        """
        
        label = Gtk.Label(xalign = xalign)
        label.set_markup(text)
        box.pack_start(label, False, True, 0)

