'''
Created: 2015

@author: mstepane@redhat.com

Dialogs for specifying actions to be performed.
'''

from gi.repository import Gtk    #@UnresolvedImport


class DialogCreatePv(Gtk.Dialog):
    
    def __init__(self, element, main_window):
        
        Gtk.Dialog.__init__(self, 'Creating physical volume', main_window, 0, 
                            ('Perform', 1, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL),
                            border_width=5)
        
        self.set_default_size(350, 150)
        
        
        label = Gtk.Label(xalign=0)
        
        text = 'Action to perform:\n\
        create physical volume on <i>%s</i>' %element['name']
        
        label.set_markup(text)


        label_commands = Gtk.Label(xalign=0)
        
        text = 'Corresponding sequence of commands:\n\
        <tt><small>pvcreate /dev/%s</small></tt>' %element['name']
        
        label_commands.set_markup(text)
        label_commands.set_margin_bottom(20)
        
        
        expander = Gtk.Expander()
        expander.add(label_commands)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(5)
        box.set_margin_left(5)
        box.add(label)
        box.add(expander)
        
        self.show_all()
        
        
class DialogRemovePvFromVg(Gtk.Dialog):
    
    def __init__(self, pv, main_window):
        
        Gtk.Dialog.__init__(self, 'Removing physical volume from volume group', 
                            main_window, 0,
                            ('Perform', 1, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL), 
                            border_width=5)
        
        self.set_default_size(350, 150)
        
        
        label = Gtk.Label(xalign=0)
        
        text = 'Action to perform:\n\
        remove physical volume <i>%s</i> from volume group <i>%s</i>' %(
                                            pv['label']['name'],pv['vg_name'])
        
        label.set_markup(text)


        label_commands = Gtk.Label(xalign=0)
        
        text = 'Corresponding sequence of commands:\n\
        <tt><small>vgreduce %s %s</small></tt>' %(pv['vg_name'],pv['name'])
        
        label_commands.set_markup(text)
        label_commands.set_margin_bottom(20)
        
        
        expander = Gtk.Expander()
        expander.add(label_commands)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(5)
        box.set_margin_left(5)
        box.add(label)
        box.add(expander)
        
        self.show_all()
        

class DialogAddToVg(Gtk.Dialog):
    
    def __init__(self, pv, main_window):
        
        Gtk.Dialog.__init__(self, 'Adding physical volume to volume group', 
                            main_window, 0,
                            ('Perform', 1, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL), 
                            border_width=5)
        
        self.set_default_size(400, 150)
        
        
        label1 = Gtk.Label('Action to perform:', xalign=0)
        
        label2 = Gtk.Label(xalign=0)
        text = 'add physical volume <i>%s</i> to volume group '%pv['label']['name']
        label2.set_markup(text)
        
        
        vgs = main_window.vgs
        self.combo = Gtk.ComboBoxText()
        
        for vg in vgs:
            self.combo.append_text(vg['name'])
        
        self.combo.set_active(0)
        
        label_commands = Gtk.Label(xalign=0)
        
        text = 'Corresponding sequence of commands:\n\
        <tt><small>vgextend VG_NAME %s</small></tt>' %pv['name']
        
        label_commands.set_markup(text)
        label_commands.set_margin_bottom(20)
        
        
        expander = Gtk.Expander()
        expander.add(label_commands)

        
        hbox = Gtk.Box()
        hbox.add(label2)
        hbox.add(self.combo)

        box = self.get_content_area()
        box.set_margin_top(5)
        box.set_margin_left(5)
        
        box.add(label1)
        box.add(hbox)
        box.add(expander)
        
        self.show_all()
        
        
class DialogVgExtend(Gtk.Dialog):
    
    def __init__(self, vg, main_window):
        
        Gtk.Dialog.__init__(self, 'Extending volume group with physical volume', 
                            main_window, 0,
                            ('Perform', 1, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL), 
                            border_width=5)
        
        self.set_default_size(400, 150)
        
        
        label1 = Gtk.Label('Action to perform:', xalign=0)
        
        label2 = Gtk.Label(xalign=0)
        text = 'extend volume group <i>%s</i> with physical volume ' %vg['name']
        label2.set_markup(text)
        
        
        pvs = main_window.pvs
        self.combo = Gtk.ComboBoxText()
        
        for pv in pvs:
            if not pv['vg_name']:
                self.combo.append_text(pv['label']['name'])
        
        self.combo.set_active(0)
        
        label_commands = Gtk.Label(xalign=0)
        
        text = 'Corresponding sequence of commands:\n\
        <tt><small>vgextend %s PV_NAME</small></tt>' %vg['name']
        
        label_commands.set_markup(text)
        label_commands.set_margin_bottom(20)
        
        
        expander = Gtk.Expander()
        expander.add(label_commands)

        
        hbox = Gtk.Box()
        hbox.add(label2)
        hbox.add(self.combo)

        box = self.get_content_area()
        box.set_margin_top(5)
        box.set_margin_left(5)
        
        box.add(label1)
        box.add(hbox)
        box.add(expander)
        
        self.show_all()
        
        
class DialogVgReduce(Gtk.Dialog):
    
    def __init__(self, vg, main_window):
        
        Gtk.Dialog.__init__(self, 'Removing physical volume from volume group', 
                            main_window, 0,
                            ('Perform', 1, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL), 
                            border_width=5)
        
        self.set_default_size(400, 150)
        
        
        label1 = Gtk.Label('Action to perform:', xalign=0)
        
        label2 = Gtk.Label(xalign=0)
        text = 'From volume group <i>%s</i> remove physical volume ' %vg['name']
        label2.set_markup(text)
        
        
        pvs = main_window.pvs
        self.combo = Gtk.ComboBoxText()
        
        for pv in pvs:
            if pv['vg_name'] == vg['name']:
                self.combo.append_text(pv['label']['name'])
        
        self.combo.set_active(0)
        
        label_commands = Gtk.Label(xalign=0)
        
        text = 'Corresponding sequence of commands:\n\
        <tt><small>vgreduce %s PV_NAME</small></tt>' %vg['name']
        
        label_commands.set_markup(text)
        label_commands.set_margin_bottom(20)
        
        
        expander = Gtk.Expander()
        expander.add(label_commands)

        
        hbox = Gtk.Box()
        hbox.add(label2)
        hbox.add(self.combo)

        box = self.get_content_area()
        box.set_margin_top(5)
        box.set_margin_left(5)
        
        box.add(label1)
        box.add(hbox)
        box.add(expander)
        
        self.show_all()


class DialogRemoveElement(Gtk.Dialog):
    
    def __init__(self, element, main_window):
        
        Gtk.Dialog.__init__(self, 'Removing the storage element', 
                            main_window, 0,
                            ('Perform', 1, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL), 
                            border_width=5)
        
        self.set_default_size(350, 150)
        
        
        label = Gtk.Label(xalign=0)
        
        element_type = element['label']['type']['long']
        element_type = element_type[0].lower() + element_type[1:]
        text = 'Action to perform:\n\
        remove %s <i>%s</i>' %(element_type, element['label']['name'])
        
        label.set_markup(text)


        label_commands = Gtk.Label(xalign=0)
        
        text = 'Corresponding sequence of commands:\n\
        <tt><small>pvremove %s</small></tt>' %element['name']
        
        label_commands.set_markup(text)
        label_commands.set_margin_bottom(20)
        
        
        expander = Gtk.Expander()
        expander.add(label_commands)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(5)
        box.set_margin_left(5)
        box.add(label)
        box.add(expander)
        
        self.show_all()
        
