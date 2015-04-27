'''
Created: 2015

@author: mstepane@redhat.com

Icons representing features of storage elements.
'''

from gi.repository import GdkPixbuf #@UnresolvedImport

from data.utils import get_by_uuid

FS_TYPES = ['ext3', 'ext4', 'vfat', 'ntfs', 'btrfs', 'xfs']


class Icons:
    """Icons representing features of storage elements.
    """
    
    def __init__(self, all_elements):
        
        self.all_elements = all_elements
        
        pixbuf = GdkPixbuf.Pixbuf()
        
        self.free = pixbuf.new_from_file_at_size('graphics/free.png', 10, 10)
        self.pv = pixbuf.new_from_file_at_size('graphics/pv.png', 10, 10)
        self.mount = pixbuf.new_from_file_at_size('graphics/mount.png', 10, 10)
        self.fs = pixbuf.new_from_file_at_size('graphics/fs.jpg', 9, 9) 
        self.crypt = pixbuf.new_from_file_at_size('graphics/crypt.png', 10, 12)
        self.menu = pixbuf.new_from_file_at_size('graphics/menu.png', 13, 13)
        
    
    def assign_icon(self, elem):
        """Given a storage element returns appropriate icon.
        """
        
        short_type = elem['label']['type']['short']
        
        icon = self.free
        
        if elem['mountpoint']:
            icon = self.mount
            
        elif elem['fstype'] in FS_TYPES:
            icon = self.fs
        
        elif elem['children']:
            child = get_by_uuid(elem['children'][0], self.all_elements)
            
            if child and child['type'] == 'pv':
                icon = self.pv
            else:
                icon = None
        
        elif short_type in ['Cache', 'VG'] or short_type.startswith('Thin pool'):
            icon = None
        
        
        return icon
    
    