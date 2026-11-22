"""Explicit owner-operated read-only native probe. Never starts copying or trades."""
import argparse,json,os,stat,sys
from pathlib import Path
from exness_adapter import ExnessAdapter,AdapterError

def load_private(path):
 path=Path(path)
 info=path.lstat()
 if path.is_symlink() or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode)&0o077:raise AdapterError('Use an owner-only regular private configuration file (0600)')
 if info.st_size>65536:raise AdapterError('Private configuration too large')
 value=json.loads(path.read_text())
 if set(value)!={'gateway','account_id','api_key','private_key'}:raise AdapterError('Private config requires gateway/account_id/api_key/private_key only')
 return value

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',required=True);parser.add_argument('--allow-read-only-network',action='store_true');args=parser.parse_args()
 if not args.allow_read_only_network:parser.error('Explicit --allow-read-only-network is required; no request was sent')
 config=load_private(args.config)
 client=ExnessAdapter(config['gateway'],config['api_key'],config['private_key'])
 info=client.account(config['account_id']);limits=client.limits(config['account_id']);snapshot=client.snapshot(config['account_id'])
 # Summary only: no private keys, signed headers, full account data or transaction values.
 print(json.dumps({'adapter':'exness-native-read-only','account_id':info['account_id'],'currency':info['settings']['currency'],'orders_count':len(snapshot['orders']),'positions_count':len(snapshot['positions']),'limits_received':isinstance(limits,dict),'writes_enabled':False,'copy_engine':'synthetic-only; native engine integration remains open'},indent=2))
if __name__=='__main__':
 try:main()
 except (AdapterError,OSError,ValueError,KeyError):
  print('Read-only probe failed; check private configuration, account scope, permissions and connectivity. No trading request was sent.',file=sys.stderr);raise SystemExit(1)
