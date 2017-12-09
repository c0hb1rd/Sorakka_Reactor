import zmq


class BaseZmq:
    def __init__(self, zmq_type):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq_type)

    def bind(self, protocal, host, port):
        print('* Server bind in ({protocal}://{host}:{port})'.format(protocal=protocal, host=host, port=port))

        self.socket.bind("{protocal}://{host}:{port}".format(protocal=protocal, host=host, port=port))

    def connect(self, protocal, host, port):
        print('* Server connect in ({protocal}://{host}:{port})'.format(protocal=protocal, host=host, port=port))

        self.socket.connect("{protocal}://{host}:{port}".format(protocal=protocal, host=host, port=port))

    def close(self):
        self.socket.close()

    def send(self, data):
        self.socket.send_multipart(data)

    def recv(self):
        return self.socket.recv_multipart()

    def run(self):
        raise NotImplemented


class ZmqREP(BaseZmq):
    def __init__(self):
        super().__init__(zmq.REP)


class ZmqREQ(BaseZmq):
    def __init__(self):
        super().__init__(zmq.REQ)


class ZmqRouter(BaseZmq):
    def __init__(self):
        super().__init__(zmq.ROUTER)


class ZmqDealer(BaseZmq):
    def __init__(self):
        super().__init__(zmq.DEALER)
