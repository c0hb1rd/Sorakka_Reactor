import time

DEFAULT_RET = {'ok': 1}
msg_queue = []


def error_log(path, detail):
    now = time.asctime()
    with open(path, 'a') as f:
        f.write(
            "ERROR\t{time}\t{detail}\n".format(time=now, detail=detail)
        )


def response(data, kind):
    ret = {'ok': kind}

    if isinstance(data, dict):
        ret.update(data)

    return ret


def success(data):
    return response(data, 1)


def error(data):
    return response(data, 0)


def set_recv_ret(data):
    if not isinstance(data, dict):
        return
    DEFAULT_RET.update(data)


def recv_handler(f, timeout=1, ret: dict = None):
    def decorator(obj, *args, **kwargs):
        msg = f(obj, *args, **kwargs)

        time.sleep(timeout)

        if ret is None:
            set_recv_ret({'data': msg})
            obj.socket.send_json(DEFAULT_RET)
        else:
            obj.socket.send_json(ret)

        return msg

    return decorator


def capture(f):
    def decorator(obj, request, *args, **kwargs):
        try:
            header, ret = f(obj, request, *args, **kwargs)
        except Exception as e:
            header, _ = request

            error_msg = str(e)
            print("* ERROR", error_msg)
            error_log(obj.error_log_path, error_msg)

            ret = ''
            header['status'] = 0x00000001

        return header, ret

    return decorator
