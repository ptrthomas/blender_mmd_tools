import sys

PYDEV_SOURCE_DIR = "/Applications/LiClipse.app/Contents/liclipse/plugins/org.python.pydev_4.5.4.201601292050/pysrc"

bl_info = {"name": "Debug Mode", "category": "Object"}

def register():
    argv = sys.argv
    try:
        argv = argv[argv.index("--") + 1:]
        if "debug" not in argv:
            raise ValueError("")
    except ValueError:
        print("debug mode plugin - debug mode not set on command line, normal startup")
        return
        
    print("debug mode plugin - attempting to connect to python debug server")
    if PYDEV_SOURCE_DIR not in sys.path:
        sys.path.append(PYDEV_SOURCE_DIR)
    import pydevd
    pydevd.settrace() 
    print("debug mode plugin - started debug mode")   
    
def unregister():
    print("debug mode plugin - unregister")
