"""Offline generated-key checks; no broker calls or real keys."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

p=Path(__file__).resolve().parents[1]/'assets/exness_signing.py'
spec=importlib.util.spec_from_file_location('candidate_signing',p);signing=importlib.util.module_from_spec(spec);spec.loader.exec_module(signing)
decode=lambda x:base64.urlsafe_b64decode(x+'='*((-len(x))%4))
key=Ed25519PrivateKey.generate();seed=key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption());public=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
assert signing.load_key((seed+public).hex()).public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)==public
for method,path,body,identity in [('GET','/v1/trading/access-point?account_id=123',b'',''),('POST','/v1/trading/accounts/123/positions',b'{"volume":"0.02"}','synthetic-request-1')]:
 h=signing.headers('dummy',key,method,path,body,identity,timestamp_ms=123456)
 raw=decode(h['EXN-DATA']);data=json.loads(raw);key.public_key().verify(decode(h['EXN-SIGN']),raw)
 assert data['path']==path and data['body_hash']==signing.b64(hashlib.sha256(body).digest()) and data['idempotency_key']==identity
 assert '=' not in h['EXN-DATA'] and '=' not in h['EXN-SIGN']
 try:key.public_key().verify(decode(h['EXN-SIGN']),raw+b' ')
 except InvalidSignature:pass
 else:raise AssertionError('Tampered bytes accepted')
for operation in [lambda:signing.load_key((seed+b'0'*32).hex()),lambda:signing.headers('dummy',key,'GET','/x',request_id='wrong'),lambda:signing.headers('dummy',key,'POST','/x'),lambda:signing.headers('dummy',key,'GET','/x?a=1&a=2')]:
 try:operation()
 except ValueError:pass
 else:raise AssertionError('Invalid input accepted')
print(json.dumps({'result':'passed','scope':'offline generated-key signing only','network_access':False,'real_broker_adapter_accepted':False}))
