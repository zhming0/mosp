import platform

def create_setter():
    if "Darwin" == platform.system():
        import proxysetter.darwin
        return proxysetter.darwin.DarwinProxySetter()

class ProxySetter():

    def backup(self):
        pass
    
    def modify(self, addr, port):
        pass

    def restore(self):
        pass
