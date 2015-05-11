'''
Created: 2015

@author: mstepane@redhat.com

Actions to perform when various signals are emitted.
'''


def destroy_children(widget):
        """Destroys all children of a given widget.
        """
        
        children = widget.get_children()
        
        for child in children:
            
            child.destroy()
            

def clear_dependencies(main_window):
        """Unhiglights all rectangles.
        """
        
        rectangles = main_window.scheme_box.rectangles
        
        for rec in rectangles.itervalues():
            
            rec.set_name('Rectangle')
            
