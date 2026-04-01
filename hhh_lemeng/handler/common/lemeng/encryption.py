import base64
import urllib.parse

ENCRYPT_CONFIG_KEY = "ac1f5adfa1acc712321fb211231a109d12f61"


def decode_data(decode_str: str, key=ENCRYPT_CONFIG_KEY) -> str:
    # 默认密钥，可替换为你实际使用的 key
    # key = "your_default_key_here"

    # 解码两次 URL 编码（相当于 JavaScript 的 decodeURIComponent）
    decode_str = urllib.parse.unquote(decode_str)

    # base64 解码 + 解码 escape 编码（escape 在 JS 中等价于 Latin-1 编码）
    decode_bytes = base64.b64decode(decode_str)
    decode_str = decode_bytes.decode("latin-1")  # JS 的 escape -> Latin-1

    retstr = ""
    strlen = len(decode_str)
    keylen = len(key)

    for i in range(strlen):
        substr = decode_str[i]
        subkey = key[i % keylen]
        xor_char = ord(substr) ^ ord(subkey)
        # 如果 XOR 后为 0，保留原字符；否则转换成字符
        ret = chr(xor_char) if xor_char != 0 else substr
        retstr += ret

    # 最后再进行一次 URL 解码
    return urllib.parse.unquote(retstr)


def decode_data2(decode_str: str, key=ENCRYPT_CONFIG_KEY) -> str:
    decodeStr = urllib.parse.unquote(decode_str)

    decoded_bytes = base64.b64decode(decodeStr)
    atob_str = "".join(chr(b) for b in decoded_bytes)
    escaped_str = "".join("%{:02X}".format(ord(ch)) for ch in atob_str)
    decodeStr = urllib.parse.unquote(escaped_str)

    retstr = ""
    strlen = len(decodeStr)
    keylen = len(key)
    for i in range(strlen):
        current_char = decodeStr[i]
        key_char = key[i % keylen]
        xor_val = ord(current_char) ^ ord(key_char)
        retstr += chr(xor_val) if xor_val != 0 else current_char

    retstr = urllib.parse.unquote(retstr)

    return retstr
