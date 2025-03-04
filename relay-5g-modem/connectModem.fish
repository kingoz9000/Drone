function connectModem
echo 'hello'

#uncomment these 4 lines below if first time using this script.
#sudo systemctl enable NetworkManager
#sudo systemctl start NetworkManager
#sudo systemctl enable ModemManager
#sudo systemctl start ModemManager

set input (mmcli -L)
echo $input

#set number $input | grep -P '\d+ (?=[Quectel])' -o #this doesnt work
set number (echo $input | grep -oE '/Modem/([0-9]+)' | grep -oE '[0-9]+') #this works
echo $number

sudo mmcli -m $number --enable --timeout=180
sudo mmcli -m $number --simple-connect="apn=internet"

sudo nmcli connection add type gsm ifname '*' #con-name aau-modem apn "internet"
sudo mmcli -m $number
nmcli device
end
