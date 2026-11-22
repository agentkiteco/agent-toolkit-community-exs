"""Offline-capable signing primitive, not a network/production adapter."""
import base64
import hashlib
import json
import time
from urllib.parse import parse_qsl, urlsplit
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def b64(raw):return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def load_key(value):
    value=value.strip()
    if value.startswith('-----BEGIN PRIVATE KEY-----'):
        key=serialization.load_pem_private_key(value.encode(),password=None)
        if not isinstance(key,Ed25519PrivateKey):raise ValueError('Ed25519 key required')
        return key
    try:raw=bytes.fromhex(value.removeprefix('0x'))
    except ValueError:raise ValueError('Invalid private key format') from None
    if len(raw) not in (32,64):raise ValueError('Use a32-byte seed or64-byte seed/public pair')
    key=Ed25519PrivateKey.from_private_bytes(raw[:32])
    if len(raw)==64 and key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)!=raw[32:]:raise ValueError('Private key public half mismatch')
    return key


def headers(api_key,key,method,path,body=b'',request_id='',timestamp_ms=None):
    if not isinstance(body,bytes):raise ValueError('Serialize body once as bytes before signing')
    url=urlsplit(path)
    if not path.startswith('/') or url.scheme or url.netloc or url.fragment:raise ValueError('Use exact path/query, not a host URL')
    pairs=parse_qsl(url.query,keep_blank_values=True)
    if len({name for name,_ in pairs})!=len(pairs):raise ValueError('Duplicate query parameters are unsupported')
    method=method.upper()
    if method not in {'GET','POST','PATCH','PUT','DELETE'}:raise ValueError('Unsupported HTTP method')
    if method=='GET' and (request_id or body):raise ValueError('Signed GET requires empty request ID and body')
    if method!='GET' and not request_id:raise ValueError('Persist mutation identity before signing')
    if not isinstance(api_key,str) or not api_key:raise ValueError('API key required')
    stamp=int(time.time()*1000) if timestamp_ms is None else timestamp_ms
    if type(stamp) is not int or stamp<0:raise ValueError('Nonnegative integer timestamp required')
    payload=json.dumps({'api_key':api_key,'idempotency_key':request_id,'timestamp':stamp,'sign_version':1,'method':method,'path':path,'body_hash':b64(hashlib.sha256(body).digest())},ensure_ascii=False,separators=(',',':')).encode()
    return {'EXN-API-KEY':api_key,'EXN-IDEMPOTENCY-KEY':request_id,'EXN-TIMESTAMP':str(stamp),'EXN-SIGN-VERSION':'1','EXN-DATA':b64(payload),'EXN-SIGN':b64(key.sign(payload))}
