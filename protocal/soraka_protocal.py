import msgpack

STKRET_SOK = '0x00000000'  # 成功，一切正常
STKRET_SFALSE = '0x00000001'  # 成功，有异常

STKRET_EGENERAL = '0x80000001'  # 失败，未知原因
STKRET_EUNKNOWN = '0x80000001'  # 失败，未知原因
STKRET_EPARAMETER = '0x80000002'  # 失败，无效参数
STKRET_EPRIVILEGE = '0x80000003'  # 失败，没有权限
STKRET_ENOTIMPL = '0x80000004'  # 失败，方法未实现
STKRET_ETIMEOUT = '0x80000005'  # 失败，超时

STKRET_ENOTEXISTS = '0x80000010'  # 失败，目标不存在
STKRET_EEXISTS = '0x80000011'  # 失败，目标已存在
STKRET_ENETWORK = '0x80000012'  # 失败，网络异常

STKRET_ECONNRESET = '0x80001001'  # 失败，连接被重置
STKRET_EINVALIDMSG = '0x80001002'  # 失败，无效 ROC 消息

NOTICE = 1
REQUEST = 2
RESPONSE = 3


def decode(obj):
    if isinstance(obj, dict):
        ret = {}
        for k, v in obj.items():
            ret[k.decode() if isinstance(k, bytes) else k] = v.decode() if isinstance(v, bytes) else v
        return ret
    if isinstance(obj, list):
        return [item.decode() if isinstance(item, bytes) else decode(item) for item in obj]
    return obj


def gen_header(msg_type, header):
    return msgpack.packb({
        "msgType": msg_type,  # 1 is notice, 2 is request, 3 is response
        "id": header['id'] if msg_type is RESPONSE else 0,  # request id
        "sender": [],
        "target": header['target'] if msg_type is RESPONSE or msg_type is REQUEST else [],  # request target
        "service": header['service'],  # request service
        "routine": header['routine'],  # request routine
        "srcIP": "",  # None
        "status": header['status'] if msg_type is RESPONSE else 0x00000000  # 0 success,  1
    })


def generate_multipart(msg_type, header, payload):
    header = gen_header(msg_type, header)

    if payload is None:
        payload = []

    return ['STKMSG'.encode(), header, msgpack.packb(payload)]


def parse_multipart(multipart):
    _, header, payload = multipart
    return msgpack.unpackb(header, object_hook=decode), msgpack.unpackb(payload, list_hook=decode,
                                                                        object_hook=decode) if payload != b'' else payload
