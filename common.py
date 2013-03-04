import traceback
import sys
from const import *

def printexc(limit=7):
	if DEBUG == False: return
	exc_type, exc_value, exc_traceback = sys.exc_info()
	traceback.print_exception(exc_type, exc_value, exc_traceback,
										limit=limit, file=sys.stdout)
def log(data):
	if DEBUG == False: return
	print data
	
def printbytes(data):
	for i in data:
		print ord(i),
	print ""
