import time
from threading import Thread

from zmq_reactor import handler, ZmqDealer, zmq
from zmq_reactor.protocal import soraka_protocal


class SorakaReactor(ZmqDealer):
    def __init__(self, error_path='./error.log'):
        super().__init__()
        self.services = []
        self.services_map = {}
        self.error_log_path = error_path
        self.start_heartbeat = True
        self.stop_heartbeat = False
        self.sub_list = []
        self.main_proc = None
        self.proc_flag = None
        self.reactor = self.socket
        self.debug = False
        self.lock = False

    def insert_into_thead(self, routine):
        self.sub_list.append(routine)

    def handler_routine(self, service, routinue, func):
        if service not in self.services_map:
            self.services_map[service] = {}
            self.services.append(service)

        if routinue in self.services_map[service].keys():
            raise Exception("Routine exist")

        self.services_map[service][routinue] = func

    def parse_multipart(self, request):
        if not request[0].decode():
            return ''
        return soraka_protocal.parse_multipart(request)

    def send_notice(self, data, payload=None):
        multipart = soraka_protocal.generate_multipart(soraka_protocal.NOTICE, data, payload)
        self.send(multipart)

    def send_request(self, data, payload=None):
        multipart = soraka_protocal.generate_multipart(soraka_protocal.REQUEST, data, payload)

        while self.lock:
            continue

        self.send(multipart)

        self.lock = True
        self.recv()
        self.lock = False

    def send_response(self, header, payload=None):
        multipart = soraka_protocal.generate_multipart(soraka_protocal.RESPONSE, header, payload)
        self.send(multipart)

    def send_heartbeat(self):
        header = {
            'service': 'Engine',
            'routine': 'reactorHeartBeat',
        }

        def work(obj):
            if not obj.start_heartbeat:
                return
            obj.start_heartbeat = False
            while True:
                time.sleep(10)
                if obj.stop_heartbeat:
                    break
                obj.send_notice(header, obj.services)

        Thread(target=work, args=(self,)).start()

    def send_register(self):
        header = {
            'service': 'Engine',
            'routine': 'reactorRegister',
        }

        payload = {
            'reactorID': [],
            'lastHeartBeat': 0,
            'payload': 0,
            'serviceList': self.services
        }

        self.send_notice(header, payload)

    def register_service(self, obj):
        for rule in obj.rules:
            self.handler_routine(rule['service'], rule['routine'], rule['func'])

    @handler.capture
    def dispacth_request(self, request):

        header, payload = request

        service = header['service']
        routine = header['routine']

        if service not in self.services_map:
            raise Exception("Service no exist")

        if routine not in self.services_map[service].keys():
            raise Exception("Routine no exist")

        header, ret = self.services_map[service][routine](header, payload, socket=self)

        return header, ret

    def init_proc(self):
        self.main_proc = self.context.socket(zmq.DEALER)
        self.main_proc.bind("inproc://" + self.proc_flag)

    def proc_worker(self, request):
        worker = self.context.socket(zmq.DEALER)
        worker.connect("inproc://" + self.proc_flag)

        header, payload = self.dispacth_request(request)

        multipart = soraka_protocal.generate_multipart(soraka_protocal.RESPONSE, header, payload)

        worker.send_multipart(multipart)

    def close(self):
        self.reactor.close()
        if self.main_proc is not None:
            self.main_proc.close()
        self.console_prompt('* Close Server')

    def console_prompt(self, msg):
        if self.debug:
            print(msg)

    def run(self, debug=False):
        self.debug = debug

        self.console_prompt('* Into loop...')
        self.console_prompt(self.services_map)

        try:
            while True:
                multiparts = self.recv()

                request = self.parse_multipart(multiparts)
                print(request)

                if not request:
                    self.send_register()
                    self.send_heartbeat()
                    continue

                header, payload = self.dispacth_request(request)

                print('send', header, payload)

                self.send_response(header, payload)
        except KeyboardInterrupt:
            self.stop_heartbeat = True
            self.close()
            self.console_prompt('* Exit')

    def run_poll(self, proc_flag, debug=False):
        self.proc_flag = proc_flag
        self.debug = debug

        self.console_prompt('* Into poll loop...')
        if self.debug:
            for service in self.services_map:
                self.console_prompt(service + ' ' + str(list(self.services_map[service].keys())))

        poller = zmq.Poller()

        self.init_proc()

        poller.register(self.reactor, zmq.POLLIN)
        poller.register(self.main_proc, zmq.POLLIN)

        try:
            while True:
                socks = dict(poller.poll())

                if self.main_proc in socks and socks[self.main_proc] == zmq.POLLIN:
                    result = self.main_proc.recv_multipart()
                    self.console_prompt('[*]Worker Center received worker result')

                    self.reactor.send_multipart(result)
                    self.console_prompt('[*]Reactor send result to Soraka GateWay')

                if self.reactor in socks and socks[self.reactor] == zmq.POLLIN:
                    self.console_prompt('[*]Reactor received request')
                    multiparts = self.recv()

                    request = self.parse_multipart(multiparts)

                    if len(request) > 0:
                        print(time.ctime(), '\tService:', request[0]['service'], '\tRoutine:',
                              request[0]['routine'] + '\n')

                    if not request:
                        self.send_register()
                        self.send_heartbeat()
                        continue

                    re_header, re_payload = request

                    service = re_header['service']
                    routine = re_header['routine']

                    if routine in self.sub_list:
                        self.console_prompt('[*]Request send to Worker Center')
                        Thread(target=self.proc_worker, args=(request,)).start()
                    else:
                        header, payload = self.dispacth_request(request)

                        self.send_response(header, payload)
        except BaseException as e:
            print(e)
            self.close()
