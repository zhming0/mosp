from _base import ProxySetter 
from subprocess import check_output 
import subprocess
import json
import os

class DarwinProxySetter(ProxySetter):
    
    def backup(self):
        if 'mosp.backup' in os.listdir("/etc"):
            return
        backupfile = None
        try: 
            backupfile = open("/etc/mosp.backup", "w+")
            services = self.getallnetworkservices()
            conf = {}
            for service in services:
               conf[service] = self.getproxysettingbyservices(service)
            jsonconf = json.dumps(conf)
            backupfile.write(jsonconf)
        except Exception as e:
            print "backup failed: ", e
        finally:
            if backupfile: backupfile.close()


    def modify(self, addr, port):
        services = self.getallnetworkservices()
        for service in services:
            self.setproxyforservice(service, addr, port, True)

    def restore(self):
        backupfile = None
        try:
            backupfile = open("/etc/mosp.backup", "r")
            backup = json.loads(backupfile.read())
            services = self.getallnetworkservices()
            for service in services:
                conf = backup[service]
                self.setproxyforservice(service, conf['server'], conf['port'], conf['enabled'])
        except Exception as e:
            print "restore failed: ", e
        finally:
            if backupfile: 
                backupfile.close()
                os.remove("/etc/mosp.backup")

    def setproxyforservice(self, service, domain, port, switch):
        try:
            subprocess.check_output(["networksetup", "-setsocksfirewallproxy", service, domain, port])
            tmp = "off"
            if switch: tmp = "on"
            subprocess.check_output(["networksetup", "-setsocksfirewallproxystate", service, tmp])
        except Exception as e:
            print "setproxyforservice failed: ", e

    def getallnetworkservices(self):
        try:
            ret = subprocess.check_output(["networksetup", "-listallnetworkservices"])
            ret = ret.split("\n")
            ret.remove("")
            ret.remove('An asterisk (*) denotes that a network service is disabled.')
            return ret
        except Exception as e: 
            print "getallnetworkservice failed: ", e
        return []

    def getproxysettingbyservices(self, service):
        try:
            ret = subprocess.check_output(["networksetup", "-getsocksfirewallproxy", service])
            ret = ret.split("\n")
            conf = {}
            if ret[0][9] == "N":
                conf["enabled"] = False
            else:
                conf["enabled"] = True

            if len(ret[1]) <= 7:
                conf['server'] = None
            else:
                conf['server'] = ret[1][8:]

            conf['port'] = ret[2][6:]
            return conf

        except:
            print "getproxysettingbyservice failed"
        return {}
