import argparse
import curses
import fcntl
import struct
import os
import socket
import errno


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def IP_Chooser(menu_window):
    rootdir = '/sys/class/net'
    nw_dict = dict()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for _, dirs, _ in os.walk(rootdir):
        for directory in dirs:
            struct_obj = struct.Struct('256s')
            device_buffer = struct_obj.pack(directory.encode('utf-8'))

            # Get IP Address of Interface
            # (https://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter/)
            mac_address = fcntl.ioctl(sock.fileno(), 0x8927, device_buffer)
            mac_address = ''.join(['%02x:' % char for char in mac_address[18:24]])[:-1]

            # Get IP Address of Interface
            # http://man7.org/linux/man-pages/man2/ioctl_list.2.html
            # SIOCGIFADDR --> 0x8915
            # SIOCGIFBRDADDR --> 0x8919
            # SIOCGIFNETMASK --> 0x891b
            ipv4_address = None
            ipv4_netmask = None
            try:
                ipv4_address = socket.inet_ntoa(fcntl.ioctl(sock.fileno(), 0x8915, device_buffer)[20:24])
            except IOError:
                pass

            try:
                ipv4_netmask = socket.inet_ntoa(fcntl.ioctl(sock.fileno(), 0x891b, device_buffer)[20:24])
            except IOError:
                pass

            nw_dict[directory] = {
                'hwaddr': mac_address,
                'ipv4_address': ipv4_address,
                'ipv4_netmask': ipv4_netmask,
                }
    # print("\n########################################")
    # print("Please Choose an Interface for the Listener\n")

    menu_window.clear()
    wrong_counter = 1

    for inter in nw_dict:
        menu_window.addstr('\n[+] Interface: ' + inter + ' (Mac: ' + str(nw_dict[inter].get('hwaddr', 'x')) +
                           ')\n IP Address: ' + str(nw_dict[inter].get('ipv4_address', 'x')) + ' / ' +
                           str(nw_dict[inter].get('ipv4_netmask', 'x')))
        wrong_counter += 2
        # print('Interface: ' + inter + ' (Mac: ' + str(nw_dict[inter].get('hwaddr', 'x')) +
        #      ')\nIP Address: ' + str(nw_dict[inter].get('ipv4_address', 'x')) +
        #      ' / ' + str(nw_dict[inter].get('ipv4_netmask', 'x')))
        # print("--------------------------------------------")

    menu_window.refresh()

    while True:
        menu_window.addstr(wrong_counter, 0, 'Interface: ')
        menu_window.refresh()
        key = None
        listen_interface = ''
        ch_count = 0
        curses.echo()

        while not (key == curses.KEY_ENTER or key in [10, 13]):
            key = menu_window.getch()
            if (key == curses.KEY_BACKSPACE or key == 127) and ch_count > 0:
                for x in range(3):
                    key = menu_window.addstr('\b')
                    key = menu_window.delch()
                listen_interface = listen_interface[:-1]
                ch_count -= 1
            elif (key == curses.KEY_BACKSPACE or key == 127) and ch_count == 0:
                for x in range(2):
                    key = menu_window.addstr('\b')
                    key = menu_window.delch()
            else:
                listen_interface = listen_interface + str(chr(key))
                ch_count += 1

        listen_interface = listen_interface.rstrip()
        try:
            return nw_dict[listen_interface]
        except KeyError:
            menu_window.addstr(wrong_counter + 1, 0, 'Invalid Interface, please choose a valid Interfacename '
                                                     '(e.g. ' + list(nw_dict.keys())[0] + ')')
            menu_window.refresh()
            wrong_counter += 2
            continue


def port_input(menu_window):
    wrong_counter = 1
    menu_window.clear()
    menu_window.addstr(0, 0, 'Please Choose a Listening Port')

    while True:
        menu_window.addstr(wrong_counter, 0, 'Port: ')
        menu_window.refresh()
        key = None
        input_port = ''
        ch_count = 0
        curses.echo()

        while not (key == curses.KEY_ENTER or key in [10, 13]):
            key = menu_window.getch()
            if (key == curses.KEY_BACKSPACE or key == 127) and ch_count > 0:
                for x in range(3):
                    key = menu_window.addstr('\b')
                    key = menu_window.delch()
                input_port = input_port[:-1]
                ch_count -= 1
            elif (key == curses.KEY_BACKSPACE or key == 127) and ch_count == 0:
                for x in range(2):
                    key = menu_window.addstr('\b')
                    key = menu_window.delch()
            else:
                input_port = input_port + str(chr(key))
                ch_count += 1

            # input_port = input_port + str(chr(key))
            # self.menu_window.addstr(wrong_counter, 6, input_port)
            # self.menu_window.refresh()
        try:
            port = int(input_port)
            if 1023 < port < 65535:
                break
            menu_window.addstr(wrong_counter + 1, 0, 'Port has to be between 1023 and 65535!')
            menu_window.getch()
        except ValueError:
            menu_window.addstr(wrong_counter + 1, 0, 'Please choose an Integer for the Port')
            menu_window.getch()
        wrong_counter += 2
    return port


def check_port_free(IP, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind((str(IP), port))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            # print("Port is already in use")
            return False
        else:
            pass
            # something else raised the socket.error exception
            # print(e)

    s.close()
    return True


def platform_chooser(menu_window):
    wrong_counter = 1
    menu_window.clear()
    menu_window.addstr(0, 0, 'Please Choose a Platform (x86 or x64): ')

    while True:
        menu_window.addstr(wrong_counter, 0, 'Platform: ')
        menu_window.refresh()
        key = None
        platform = ''
        ch_count = 0
        curses.echo()

        while True:
            key = menu_window.getch()
            if key == curses.KEY_ENTER or key in [10, 13]:
                break
            if (key == curses.KEY_BACKSPACE or key == 127) and ch_count > 0:
                for x in range(3):
                    key = menu_window.addstr('\b')
                    key = menu_window.delch()
                platform = platform[:-1]
                ch_count -= 1
            elif (key == curses.KEY_BACKSPACE or key == 127) and ch_count == 0:
                for x in range(2):
                    key = menu_window.addstr('\b')
                    key = menu_window.delch()
            else:
                platform = platform + str(chr(key))
                ch_count += 1
        platform.rstrip()
        if platform.lower() == 'x64' or platform.lower() == 'x86':
            break
        menu_window.addstr(wrong_counter + 1, 0, f'Platform has to be x64 or x86! ({platform})')
        menu_window.getch()
        wrong_counter += 2
    return platform
