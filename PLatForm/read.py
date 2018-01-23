import time
import os
import struct
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import random
import math

DATA_SIZE = 86401
LOC_SIZE = 16
TERMINAL_NUM = 100
SAT_NUM = 48
PI = 3.14159265358979323846264338328
EARTH_RADIUS = 6375000.0
COVER_RADIUS = 2700

def ReadLocation(filename, sat_loc):
	if not os.path.isfile(filename):
		print("ERROR: %s is not a valid file." % (filename))
		return
	currtime =  int(time.time())
	f = open(filename, "rb")
	for i in range(48):
		f.seek(DATA_SIZE * LOC_SIZE * i + currtime % DATA_SIZE * LOC_SIZE)
		data = f.read(16)
		data = struct.unpack('2d', data)
		sat_loc = []
		sat_loc.append(data)
	print sat_loc[0]
	f.close()

def CalculateDistance(terminal, sat):
	a = Radian(terminal[0]) - Radian(sat[0])	
	b = Radian(terminal[1]) - Radian(sat[1])	
	distance = 2 * math.asin( math.sqrt( math.pow( math.sin(a / 2), 2) + math.cos(Radian(sat[0])) * math.cos(Radian(terminal[0])) * math.pow(math.sin(b / 2), 2) ) )
	distance = distance * EARTH_RADIUS
	if distance <= COVER_RADIUS:
		return 1
	return 0

def Radian(degree):
	return degree * PI / 180.0

if __name__ == '__main__':
	sat_loc = []
	sched = BackgroundScheduler()
	sched.add_job(func=ReadLocation, args=("orbit.bin", sat_loc), trigger='cron', second='*/1')
	sched.start()
	#ReadLocation("orbit.bin", int(time.time()), sat_loc)
	#for item in sat_loc:
		#print item
	while True:
		time.sleep(1)
