import numpy as np
import cv2,cv
import sys, time,os
from itertools import izip

#inputs
gcode_file="/var/www/upload/gcode/laser_test.gcode"
image_file="einstein.jpg"
now = time.strftime("%c")

DEBUG=False #enable/disable debugging

#load image
img = cv2.imread(image_file)
img = cv2.cvtColor(img, cv.CV_BGR2GRAY) #convert to B&W
h, w = img.shape[:2]

#step = 0.002
#depth = 0.008
#x, y = 0, 0



#define feed, High=Fast=Faint, Low=Slow=Strong
feed_movement=10000
feed_light=5000
feed_hard=1200 

feed_cut=350
delay_ms=10

desired_width=30 #mm
dpi=float(w)/desired_width #obtain DPI multiplier.
threshold=55 #50-80 min light difference
scan_skip=1 #skip one row (1/2 time)
line_skipped=0 #skips counter
mov_open=False
zig=False #start with a zig, then a zag!

#write info header
g=";FABtotum laser engraving, coded on "+ str(now) +"\n"
g= g + "G4 S1 ;1 millisecond pause to buffer the bep bep\r\nM728 ;FAB bep bep(start the print, go check the oozing and skirt lines adesion)\r\nG90 ; absolute mode\r\nG4 S1 ;1 second pause to reach the printer (run fast)\r\nG1 F10000 ;Set travel speed\r\nM107\r\n"

#Compute starting movement
y_pos=float(h/dpi)
g_string="G0 Y+"+str(y_pos)+" F"+str(feed_movement)
g = g + "G4" + "\r\n"
g = g + g_string + "\r\n"
g = g + "M6\r\n"

def val_map(x, in_min, in_max, out_min, out_max):
	return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
	
print "Now preparing ",image_file
print "Scan skipping set to: " + str(scan_skip)
print "DPI : " + str(dpi)

for row in range(h):
	#print row
	line=np.zeros(w, np.uint8)  #line array
	max=0
	pos=0
	start_pos=pos
	line=img[row,:]
	#print line

	if line_skipped<scan_skip:
		line_skipped+=1
		#skip line
		continue
		
	#compute movement
	x_mov=float(w)/dpi
	y_mov=y_pos-(float(row)/dpi)
	g_string="G0 Y"+ str(y_mov) +" F"+str(feed_movement)
	g = g + g_string + "\r\n"
	
	line_skipped=0
		
	#Add line marker
	g = g + ";LINE " + str(row) +"\r\n"
		
	#zig-zag
	if zig==True:
		#ZIG!
		#invert listing
		line=reversed(list(enumerate(line)))
		zig=False
		print "reversed line" + str(row)
	else:
		#ZAG!
		line=enumerate(line)
		zig=True
	
	#for i, e in line:
	#	print i, e
	
	#sys.exit()
	for col,value in line:
		#print col, value
	
		value=abs(255-value)
		#print "colonna" +str(col)+ "value :"+str(value)
		
		if ((abs(value-max)>=threshold) or (col==w-1) or (col==0)):
			
			if mov_open==False:
				#new segment
			 	mov_open=True
				#set a new max
				max=value
				start_pos=col
				continue
				
			if mov_open==True:
				#existing segment
				#close segment
			 	mov_open=False
				
				#proportional feed
				feedrate=val_map(max, 0, 255,feed_light,feed_hard)

				#abs movement
				pos=col+1
				start_pos=pos
				pos=float(float(pos)/dpi)

				#rounding
				pos=round(pos,3)
				feedrate=round(feedrate,2)

				g_string="G0 X"+str(pos)+" F"+str(feedrate)
				g = g + g_string + "\r\n"
					
	if DEBUG:
		#debug only one line
		print g
		sys.exit()	

g = g + "M728 ;FAB bep bep (end print)\r\nG4 S1 ;pause\r\nM7;shutdown"

#print "---------------"
#print g

#dump to file
f = open(gcode_file,"w") #opens file with name of "test.txt"
f.write(g)
f.close() 

print "Completed, gcode written to ",gcode_file

sys.exit()
