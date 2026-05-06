# wasserschwein

# connect to Bluetooth
    
    connect to HC-06
    sudo rfcomm connect 0 98:D3:11:FD:1C:0B 1
    
    send data
    picocom -b 9600 --echo /dev/rfcomm0
    picocom -b 9600 --echo --omap crcrlf --emap crcrlf /dev/rfcomm0

    
# command 
    
    F <value> motor drive forward, value range 0-255
    B <value> motor drive back, value range 0-255
    L <value> left BLCD, value range 
    R <value> right BLCD, value range

    black ESC 1000 - 2000; 1000 - stop, 2000 max, 12 pin, R<cmd>
    yellow ESC 1000
