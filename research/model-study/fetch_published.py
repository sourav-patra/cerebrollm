"""Save public source material for reported scores. No inference calls."""
import hashlib
import json
import signal
import httpx
from study import OUT,save

signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('500-second command limit')))
signal.alarm(500)
urls={
    'devstral-2505.md':'https://huggingface.co/mistralai/Devstral-Small-2505/raw/main/README.md',
    'qwen3-report.html':'https://arxiv.org/html/2505.09388v1',
    'gpt-oss-model-card.pdf':'https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf',
}
receipts=[]
with httpx.Client(timeout=90,follow_redirects=True) as client:
    for name,url in urls.items():
        r=client.get(url)
        r.raise_for_status()
        (OUT/'sources'/name).write_bytes(r.content)
        receipts.append({'path':'sources/'+name,'url':url,'sha256':hashlib.sha256(r.content).hexdigest(),'status':r.status_code})
        save('published-source-receipts.json',receipts)
        print(name,len(r.content),flush=True)
