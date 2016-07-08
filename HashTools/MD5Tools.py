# -*- coding:utf-8 -*-
import hashlib

def MD5_hash_string(string):
    md5Hashtor = hashlib.md5()
    try:
        try:
            md5Hashtor.update(string.encode("utf-8"))
        except:
            md5Hashtor.update(string)
        hash = md5Hashtor.hexdigest()
    except:
        hash = None
    return hash