#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import time

from fuse import FUSE, FuseOSError, Operations, fuse_get_context

from google.cloud import storage



class Passthrough(Operations):
    def __init__(self, root):
        self.root = root
        self.storage_client = storage.Client.from_service_account_json('shivani-pal-fall2023.json')

        # Bucket name and JSON file path within the bucket
        self.bucket_name = 'bucket-shivanipal'
        self.folder = 'test/'  

        # Initialize the bucket object
        self.bucket = self.storage_client.bucket(self.bucket_name)

    # Basic File System methods : create, open, read, write, close, mounted using fuse, intercepting and forwarding to cloud storage op
    # ================================================================================================================================

    def open(self, path, flags):
        
        full_path = self._full_path(path)
        print(f'open {full_path}')
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        print(f'create {path}')
        uid, gid, pid = fuse_get_context()
        full_path = self._full_path(path)
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        os.chown(full_path,uid,gid) #chown to context uid & gid

        # google cloud storage api calls handle
        try:
            object_path = self._full_gcloud_path(path)
            # Create a new object (file)
            blob = self.bucket.blob(object_path)
            blob.upload_from_string('')

            if blob.exists():
                print("file created")
            else:
                print('file not created')

        except Exception as e:
            print(e)
            return -1

        return fd

    def read(self, path, length, offset, fh):
        print(f'reading {path}')
    
        os.lseek(fh, offset, os.SEEK_SET)

        # google cloud storage api calls handle
        try:
            object_path = self._full_gcloud_path(path)
            blob = self.bucket.blob(object_path)
            with blob.open("r") as f:
                print(f'reading from {object_path}')
                print(f.read())
        except Exception as e:
            print(e)

        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        print('write')
        os.lseek(fh, offset, os.SEEK_SET)

        # google cloud storage api calls handle
        try:
            object_path = self._full_gcloud_path(path)
            blob = self.bucket.blob(object_path)
            buf_string = buf.decode('utf-8')  # Assuming 'utf-8' encoding
            with blob.open("w") as f:
                f.write(buf_string)
        except Exception as e:
            print(e)

        return os.write(fh, buf)

    def flush(self, path, fh):
        return os.fsync(fh)

    # close
    def release(self, path, fh):
        print('release')
        return os.close(fh)
    # There's no need to explicitly open or close the object; the read operation is performed directly on the object.
    # The management of the object's data and resources is handled by the Google Cloud Storage service, w
    # hich ensures data consistency and reliability without requiring explicit open or close operations.

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)

    # Filesystem methods
    # =======================================================

    def access(self, path, mode):
        print('access')
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def getattr(self, path, fh=None):
        print('getattr')
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        print(st)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))


    # Directory Operations - mkdir, opendir, readdir, rmdir
    # =======================================================


    def opendir(self, path):
        print('opendir')
        full_path = self._full_path(path)

        if os.path.isdir(full_path):
            print(os.listdir(full_path))
        return 0
        

    def readdir(self, path, fh):
        print('readdir')
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def rmdir(self, path):
        print('rmdir')
        full_path = self._full_path(path)

        # google cloud storage api calls handle
        try:
            g_full_path = self._full_gcloud_path(path) + '/'
            print(g_full_path)
            
            folder = self.bucket.blob(g_full_path)
            folder.delete()
            if folder.exists():
                # Return a file descriptor or handle for the newly created object
                print("folder not deleted")
            else:
                print(f'folder {g_full_path} deleted')
    
        except Exception as e:
            print(e)
            return -1


        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        print('mkdir')
        print(path, mode)

        # google cloud storage api calls handle
        try:
            g_full_path = self._full_gcloud_path(path) + '/'
            print(g_full_path)
            
            blob = self.bucket.blob(g_full_path)
            blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')
            if blob.exists():
                # Return a file descriptor or handle for the newly created object
                print("file created")
            else:
                print('file not created')
    
        except Exception as e:
            print(e)
            return -1

        return os.mkdir(self._full_path(path), mode)

    def unlink(self, path):
        print('unlink')
        
        # google cloud storage api calls handle
        try:
            g_full_path = self._full_gcloud_path(path)
            print(g_full_path)
            
            blob = self.bucket.blob(g_full_path)
            # Delete the file from the bucket
            blob.delete()

            if blob.exists():
                # Return a file descriptor or handle for the newly created object
                print("file not deleted")
            else:
                print(f'file {g_full_path} deleted')
    
        except Exception as e:
            print(e)
            return -1

        return os.unlink(self._full_path(path))

    def rename(self, old, new):
        print('rename')

        # google cloud storage api calls handle
        try:
            file_name = self._full_gcloud_path(old)
            blob = self.bucket.blob(file_name)
            # Rename the file
            new_file_name = self._full_gcloud_path(new)
            if blob.exists():
                if self.bucket.rename_blob(blob, new_file_name):
                    print(f"file renamed to {new_file_name}")
            else:
                print('file doesn\'t exist')
        except Exception as e:
            print(e)
            return -1

    
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        print('link')
        return os.link(self._full_path(name), self._full_path(target))

    def utimens(self, path, times=None):
        print('utimens')
        return os.utime(self._full_path(path), times)

    # Helpers function
    # ========================================================

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _full_gcloud_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.folder, partial)
        return path

    

def main(mountpoint, root):
    FUSE(Passthrough(root), mountpoint, nothreads=True, foreground=True, allow_other=True)


if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])