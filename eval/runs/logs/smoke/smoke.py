import os,sys,json,time
sys.path.insert(0,r'<repo>\eval')
import n2_lib as L
for model in ('phi4','haiku'):
    for arm,i in (('A0','EX-01'),('A3','EX-01'),('A3','ST-01')):
        t=time.time(); a=L.run_arm(arm,model,i); print(model,arm,i,round(time.time()-t,1),'s\n',a[:600].replace('\n',' | '),'\n')
