import mss

_SCT = None

def get_sct():
    global _SCT
    if _SCT is None:
        _SCT = mss.mss()
    return _SCT
