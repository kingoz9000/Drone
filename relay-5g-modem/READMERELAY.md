For this relay a modem "Quectel RM500Q-GL" and a Raspbarry pi 5 is used.
The steps to connect them is written below. and some additional notes

notes:
helpfull websites:https://andino.systems/andino-4g-modem/setup-via-modem-manager and https://snapcraft.io/install/modem-manager/raspbian .
modem supports 3G,4G,5G. and can use ipv4, ipv6, ipv4v6.

Step 1. Find info about the modem
user@user ~> mmcli -L
output -> /org/freedesktop/ModemManager1/Modem/2 [Quectel] RM500Q-GL
The last number is important. use it with the next command. in this case it is the number 2.
user@user ~> sudo mmcli -m 2
output -> "lots of info about the modem" 
small snippet of info = "sim   primary sim path: /org/freedesktop/ModemManager1/SIM/1"

GG
BIG GG


