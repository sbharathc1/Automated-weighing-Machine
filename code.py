import RPi.GPIO as GPIO #importing GPIO
import time             #importing time
import sys
import MySQLdb          #importing mysql
import serial           #importing serial
from hx711 import HX711 #importing HX711 class
from subprocess import call #importing system call
import paho.mqtt.client as mqtt #omporting mqtt  







#lcd setup........................................
# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
 
# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
 
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
 
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005
#lcd end...............................................




#lcd start.............................................................................................................
def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)
 
def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command
 
  GPIO.output(LCD_RS, mode) # RS
 
  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)
 
def lcd_string(message,line):
  # Send string to display
 
  message = message.ljust(LCD_WIDTH," ")
 
  lcd_byte(line, LCD_CMD)
 
  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)
#lcd end..................................................................................................................................................................

#rfid start..............................................................................................................
def get_rfid(ser):
	while(1):
		try:
			start=time.time()
			data=ser.read(12)
			end=time.time()
			if end - start < 5: #value read in 5 seconds then return value
				return data
			else:
				print "timeout"  #if value not read in 5 seconds then call timeout
				time.sleep(1) 
				ser.close()      #close serial port
				ser= serial.Serial("/dev/ttyAMA0")#re initialize serial port
				ser.baudrate=9600
				ser.timeout=10
				ser.reset_output_buffer() #reset output buffer
		except:  #exception
			print "except"  #reset the serial port and start the process again
			time.sleep(1)
			ser.close()
			ser= serial.Serial("/dev/ttyAMA0")
			ser.baudrate=9600
			ser.timeout=10
			ser.reset_output_buffer()
#rfid end........................................................................................................			
			
			
#buzzer start...................................................................................................
def buzzer_once():
	GPIO.output(4,0) #make port low
	time.sleep(.3)  #wait for .3 seconds
	GPIO.output(4,1) #make output high
	time.sleep(.3) #buzzer for .3 seconds
	GPIO.output(4,0)
	time.sleep(.3)
#end buzzer.....................................................................................................

#mode1 start...................................................................................................
def mode_one():
	A=[0,0,0,0,10,0] #array to store weights
	sum=10           #to store the sum of last 6 weights
	count=1
	val = hx.get_weight(5)#function to get weight of the object
	print val
	print "Place Tag of the item: "
	lcd_string("place RFID TAG",LCD_LINE_1)#function to print on lcd screen 
	rfid=get_rfid(ser)        #function to read rfid tag 
	rfid=rfid[:10]
	print rfid
	id1=rfid[:5]				#encoding of objects
	id2=rfid[5:10]
	while 1:					#loop until the weights gets stabilized
		try:
			val = hx.get_weight(5)  # function to get weight
			if(val > 0):
				lcd_string("weight",LCD_LINE_1)  #function to print on lcd screen
				lcd_string(str(val)+" gms",LCD_LINE_2)
			A.append(val)
			print val
			l=A.pop(0)
			sum=sum-l+val
			db = get_cur()  #database cursor
			cur = db.cursor()
			cur.execute("SELECT * FROM data WHERE rfid=%s;",[rfid])#search for the given rfid tag
			row=cur.fetchone()
			if row is not None:  #if there is an rfid in the database
				print row
				#cur.execute("INSERT INTO data (object,id1,id2,weight,rfid,image) VALUES (%s,%s,%s,%s,%s,%s);",([row[1]],[id1],[id2],[row[3]],[rfid],[row[5]]))
				#db.commit()
				test_client.publish("reverse", "Weight: "+ row[3] +", "+"Tag: "+ row[4] +".") #publish that object is found and its weight
				lcd_string("congrats ",LCD_LINE_1)  #output on lcd screen
				a=rfid+" found"
				lcd_string(a,LCD_LINE_2)
				print "found"
				db.close()
				break  #go out of while loop
			if val==sum/6 and val>0:  #check that weight is stabilized by comparing weight with average of last six values
				print val
				db = get_cur()       #connection to database
				cur = db.cursor()
				cur.execute("SELECT * FROM data WHERE id1=%s;",[id1])#search for the similar item in database based on first 5 digits of rfid(i.e encoding)
				row=cur.fetchone()
				print row
				
				if row is None:  #if there on similar item in database 
					call(["fswebcam","--fps","15","-S","8","-r","320*240",str(rfid)+".jpg"])#command to take the image of the object
					call(["sudo","mv",str(rfid)+".jpg","/var/www/html"])   #storing the object in the apache server location
					image=str(rfid)+".jpg"
					lcd_string(str("New item"),LCD_LINE_1)#output on screen
				else:
					image=str(row[5]) #if there is an item of similar kind
					lcd_string("same kind item there",LCD_LINE_1)#output on screen
				object="name"
				weight=val
				#display to lcd
				lcd_string(str(weight)+"g",LCD_LINE_2)#output on screen
				cur.execute("INSERT INTO data (object,id1,id2,weight,rfid,image) VALUES (%s,%s,%s,%s,%s,%s);",([object],[id1],[id2],[weight],[rfid],[image]))#storing the item in database with respective values
				db.commit()
				buzzer_once()#buzzer function to buzzer once
				db.close()
				test_client.publish("reverse", "Weight: "+ str(weight) +"gs , "+"Tag: "+ str(rfid) +".")#publish that the item was found
				break
		        hx.power_down()
		        hx.power_up()
			time.sleep(0.5)
		except (KeyboardInterrupt, SystemExit):
	       		cleanAndExit()
#mode1 end .......................................................................................................................


#mode2 start................................................................................................................
def mode_two():
	A=[0,0,0,0,10,0]  #array to store last six vaues of weight read
	sum=10
	count=1
	val = hx.get_weight(5)#function to get the weight of item and 5 is the gpio port number 
	print val
	print "Place Tag of any item: "
	lcd_string("Place Tag of any item: ",LCD_LINE_1)#output on screen
	rfid=get_rfid(ser)#function to read rfid
	print rfid
	rfid=rfid[:10]
	db = get_cur()
	cur = db.cursor()
	cur.execute("SELECT * FROM data WHERE rfid=%s;",[rfid])#search for the item in database
	row=cur.fetchone()
	weight=int(row[3])
	while 1:		
		try:
			val = hx.get_weight(5)#function to get weight of object
			A.append(val)
			print val
			l=A.pop(0)
			sum=sum-l+val
			if val==sum/6: #check if the value is stabilized
				a = str(int(round(val/float(weight)))) #counting the number of items based on weights
				test_client.publish("reverse", a+" item(s).")#publishing the number of items
				lcd_string("mode 2",LCD_LINE_1)#output on screen
				lcd_string(a+" items",LCD_LINE_2)
				buzzer_once()#call buzzer function to buzzer
				db.close()
				break
		        hx.power_down()
		        hx.power_up()
			time.sleep(0.5)		
		except (KeyboardInterrupt, SystemExit):
	        	cleanAndExit()
#mode2 end...............................................................................................................


#mode3 start.........................................................................................................
def mode_three():
	val = hx.get_weight(5)#function to get weight of the object
	
	while True:
		try:
			db=get_cur()
			cur=db.cursor()
			cur.execute("SELECT * FROM data1")#search database for limiting value
			row=cur.fetchone()
			weight = row[0]
			db.close()
			time.sleep(0.5)
			val = hx.get_weight(5) #get weight of the object
			hx.power_down()
			hx.power_up()
			db=get_cur()
			cur=db.cursor()
			cur.execute("UPDATE data1 SET curr=%s",[val])#udating the current weight into the databse
			print val		
			db.commit()
			db.close()
			if (val < weight):#if current weight is less than the minimum 
				test_client.publish("warning", "Low content")#publish that the content is low
				lcd_string("warning",LCD_LINE_1)
				lcd_string(str(val)+" gms",LCD_LINE_2)#output on screen
				buzzer_once()  #buzzer once 
			else:#if current weight is greater than the specified minimum
				lcd_string("safe",LCD_LINE_1)#output on screen
				lcd_string(str(val)+" gms",LCD_LINE_2)
				test_client.publish("warning", "Safe")#publish safe
		except (KeyboardInterrupt, SystemExit):
				cleanAndExit()

#mode3 end............................................................................................................


#mqtt functions......................................................................................................
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("swa_news")#sucscribe to the topic

def on_message(client, userdata, msg):
	print("["+msg.topic+"]: "+str(msg.payload))#on message on subscribed topic
	a_string = str(msg.payload)
	if (a_string == "1"):  #selecting mode1
		mode_one()
	elif (a_string == "2"):#selecting mode 2
		mode_two()
	elif (a_string == "3"):#selecting mode3
		mode_three()

def on_publish(mosq, userdata, mid):
    pass

#end mqtt functions.................................................................................................
def cleanAndExit():  #cleaning gpio port before exiting
    print "Cleaning..."
    GPIO.cleanup()
    print "Bye!"
    sys.exit()

#connection to database................................................................................................
def get_cur():
	db=MySQLdb.connect("127.0.0.1",user="root",passwd="godfather",db="project")
	return db
#end connection to DB....................................................................................................


#lcd
# Main program block
GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT) # RS
GPIO.setup(LCD_D4, GPIO.OUT) # DB4
GPIO.setup(LCD_D5, GPIO.OUT) # DB5
GPIO.setup(LCD_D6, GPIO.OUT) # DB6
GPIO.setup(LCD_D7, GPIO.OUT) # DB7
 
  # Initialise display
lcd_init()








#gpio pins used....................................................................................................

GPIO.setmode(GPIO.BCM) #initialize mode
GPIO.setwarnings(False)
GPIO.setup(4,GPIO.OUT)  #set gpio 4 aas output
GPIO.output(4,0)
ser= serial.Serial("/dev/ttyAMA0")#initiliaze ser as serial
ser.baudrate=9600#set baud rate
ser.timeout=6#set serial read time out

#references for load cell...............................................................................................
hx = HX711(5, 6)
hx.set_reading_format("LSB", "MSB")#set format of data read from serial port
hx.set_reference_unit(-401)#set reference unit.How to set this is explained in report!!!
hx.reset()
hx.tare()
#end load cell references.............................................................................................

#setup mqtt..........................................................................................................
test_client = mqtt.Client()
test_client.on_connect = on_connect
test_client.on_message = on_message
test_client.on_publish = on_publish

test_client.username_pw_set("starboy", password="godfather") #connecting to mqtt client
test_client.connect("127.0.0.1", 1883, 60)
print "---------------------------------------------------"
test_client.loop_forever()#loop to continously wait for the information on given topic
