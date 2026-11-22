"""Create new isolated Cloudflare configuration; never deploys or overwrites a target."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import secrets
import shutil
from urllib.parse import urlsplit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--account-id',required=True)
    parser.add_argument('--worker',required=True)
    parser.add_argument('--bucket',required=True)
    parser.add_argument('--origin',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{32}',args.account_id):parser.error('Cloudflare Account ID must be 32 hexadecimal characters; not a trading account number.')
    if not all(re.fullmatch('[a-z0-9][a-z0-9-]{1,61}[a-z0-9]',x) for x in (args.worker,args.bucket)):parser.error('Use distinct simple lowercase Worker/bucket names of 3 to 63 characters.')
    origin=urlsplit(args.origin)
    if origin.scheme!='https' or not origin.hostname or origin.path not in ('','/') or origin.query or origin.fragment or origin.username or origin.password or origin.port not in (None,443):parser.error('Use a recipient-owned HTTPS origin without path/query/credentials.')
    app=args.app.resolve();out=args.out.resolve()
    for name in ('cloud_entrypoint.py','cloud_state.py','requirements.txt'):
        if not (app/name).is_file():parser.error('Generated app integration missing: '+name)
    # Never overwrite a working deployment or its original encryption key.
    out.mkdir(parents=True,mode=0o700,exist_ok=False)
    assets=Path(__file__).resolve().parents[1]/'assets/cloudflare'
    for name in ('worker.js','bridge.js','bridge.test.mjs','Dockerfile'):shutil.copyfile(assets/name,out/name)
    target={'account_id':args.account_id,'worker':args.worker,'bucket':args.bucket,'origin':args.origin.rstrip('/'),'new_resources_only':True}
    config={'name':args.worker,'account_id':args.account_id,'main':'worker.js','compatibility_date':'2026-11-18','workers_dev':True,'preview_urls':False,
            'containers':[{'class_name':'AppHost','scheduling_policy':'durable_object','images':{'base':{'dockerfile':'./Dockerfile','build_context':os.path.relpath(app,out)}}}],
            'durable_objects':{'bindings':[{'name':'APP_HOST','class_name':'AppHost'}]},'exports':{'AppHost':{'type':'durable-object','storage':'sqlite'}},
            'r2_buckets':[{'binding':'BACKUPS','bucket_name':args.bucket}], 'vars':{'PUBLIC_ORIGIN':target['origin'],'APP_NAME':args.worker},
            'observability':{'enabled':True,'logs':{'enabled':True,'invocation_logs':False}}}
    (out/'wrangler.jsonc').write_text(json.dumps(config,indent=2)+'\n')
    (out/'deployment-target.json').write_text(json.dumps(target,indent=2)+'\n')
    (out/'package.json').write_text(json.dumps({'name':args.worker+'-deploy','private':True,'type':'module','scripts':{'test':'node --test bridge.test.mjs','deploy':'wrangler deploy'},'devDependencies':{'wrangler':'4.152.0'}},indent=2)+'\n')
    lock=json.loads((assets/'package-lock.template.json').read_text());lock['name']=args.worker+'-deploy';lock['packages']['']['name']=args.worker+'-deploy'
    (out/'package-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    values={'STATE_KEY':base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),'BRIDGE_TOKEN':secrets.token_urlsafe(32),'OPS_TOKEN':secrets.token_urlsafe(32),'INSTALLATION_INVITATION':secrets.token_urlsafe(24),'OWNER_PASSWORD':secrets.token_urlsafe(32)}
    fd=os.open(out/'secrets.local.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(values,f)
    (out/'.gitignore').write_text('secrets.local.json\nnode_modules/\n.wrangler/\n')
    print(json.dumps({'prepared':str(out),'target':target,'deployed':False,'secrets':'Private 0600 file created; keep its original key and exclude it from archives.'}))


if __name__=='__main__':main()
