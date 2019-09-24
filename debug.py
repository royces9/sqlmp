def debug(err):
    with open('test.txt', 'a+') as fp:
        if isinstance(err, str):
            print(err)
        else:
            for e in err:
                print(str(e), file=fp)
                                                        
