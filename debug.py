import traceback

def debug(err):
    with open('debug.txt', 'a+') as fp:
        if not isinstance(err, list):
            print(str(err), file=fp)
        else:
            for e in err:
                print(str(e), file=fp)
                                                        

            
def trace():
    err = traceback.format_exc()
    debug(err)
