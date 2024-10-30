import argparse,os,subprocess,socket,re
harvard = 'harvard' in socket.gethostname()

def fetch_files(topdir,wsname,mode=-2,asimov=-1,relaunch=True):
    #files will look like topdir/plots/[wsnames]/breakdown/muHatTable_[wsnames].(tex|txt)
    start0=wsname.find('_job')
    start1=wsname.find('_',start0+1)
    if not '_job' in wsname or start0!=wsname.rfind('_job'):
        # if the workspace doesn't have the jobnofN pattern in it, assume we've been given the non-split workspace name
        if not 'breakdown_' in wsname:
            return None
        start,end,ws,lookhere=wsname.split('breakdown_')[0],wsname.split('breakdown_')[1],'',f'{topdir}/plots/'
        for d in os.listdir(lookhere):
            if start in d and end in d and '_job0of' in d:
                if ws=='':
                    ws=d
                elif os.path.getmtime(lookhere+d)>os.path.getmtime(lookhere+ws):
                    ws=d
        if ws=='':
            return None
        wsname=ws
        start0=wsname.find('_job')
        start1=wsname.find('_',start0+1)
    front,back,njobs = wsname[0:start0],wsname[start1:],int(wsname[wsname.find('of',start0)+2:start1])
    txts,texs,broken=[],[],[]
    for i in range(njobs):
        # directory is plots/r2-asimovData_cnd1_1_normal-full.charlie_breakdown_job47of47_Run1Run2Comb_charlie/breakdown/
        # slurm_logs look like: slurm_logs/output_r2-asimovData_cnd1_1_normal-full.charlie_breakdown_job0of47_Run1Run2Comb_charlie_job0of47.log
        # first line looks like: "START {script}.sh ..."
        #d,log='{4}/plots/{0}_job{1}of{2}{3}/breakdown/'.format(front,i,njobs,back,topdir),'{4}/slurm_logs/output_{0}_job{1}of{2}{3}_job{1}of{2}.log'.format(front,i,njobs,back,topdir)
        d = f'{topdir}/{front}_job{i}of{njobs}{back}/plots/breakdown/'
        log = f'{topdir}/slurm_logs/output_{front}_job{i}of{njobs}{back}_job{i}of{njobs}.log'
        if not os.path.exists(d):
            check_log(log,relaunch)
            broken.append(d)
            continue
        for f in os.listdir(d):
            if f.find('muHatTable')==0 and (mode<-1 or f'mode{mode}' in f) and (asimov<0 or f'Asimov{asimov}' in f) and (mode==-1 or (not 'mode-1' in f)):
                if f.endswith('.txt'):
                    txts.append(d+f)
                if f.endswith('.tex'):
                    texs.append(d+f)
    return txts,texs,f'{topdir}/{front}{back}/plots/breakdown/',njobs,broken

def check_log(log,relaunch):
    if not os.path.exists(log):
        return False
    buff = subprocess.Popen(['grep','-a',"START",log], stdout=subprocess.PIPE).stdout.read() # -a lets grep read a file it thinks is binary
    fin = subprocess.Popen(['grep','-a',"FINISH",log], stdout=subprocess.PIPE).stdout.read() # -a lets grep read a file it thinks is binary
    error = subprocess.Popen(['grep','-a',"[Ee]rror",log], stdout=subprocess.PIPE).stdout.read() # -a lets grep read a file it thinks is binary
    if len(buff)>0:
        script = buff.split(' ')[1]
        cmd=["sbatch","--mem",'32000',"--time","7-0:0:0","-p",'pleiades','-e',log,'-o',log,script] if harvard else ['bsub','-q','2nd','-o',log,'sh',runfile]
        if (len(fin)>0 and relaunch) or error:
            subprocess.Popen(cmd).wait()
            return False
        else:
            print('No tables for but no finish indicated in ',log,'...consider running ',' '.join(cmd))
            return True
    return False

def concat_txts_texs(txts,texs,dire,njobs):
    if not os.path.exists(dire):
        os.makedirs(dire)
    txtnm,texnm=txts[0].replace(f'_job0of{njobs}',''),texs[0].replace(f'_job0of{njobs}','')
    scan_for_abs_frac(txts,txtnm,njobs)
    scan_for_abs_frac(texs,texnm,njobs)
    return txtnm,texnm

def fetch_and_merge(topdir,wsname,mode=-2,asimov=-1):
    stuff = fetch_files(topdir,wsname,mode,asimov)
    if stuff is None:
        return ['none']
    elif len(stuff[0])==0:
        return ['none']

    POIs = { re.sub(r'\.txt$', '', re.search(r'(SigXsecOverSM|c).*\.txt$',f).group()) for f in stuff[0]}
    print('POIs',POIs)
    for poi in POIs:
        stuff0 = [ txt for txt in stuff[0] if re.match(fr'.*{poi}\.txt$', txt)]
        stuff1 = [ tex for tex in stuff[1] if re.match(fr'.*{poi}\.tex$', tex)]
        one,two = concat_txts_texs(stuff0,stuff1,stuff[2],stuff[3])
        retme = [one,two]+stuff[4]
        print('The following jobs failed and were relaunched: ')
        for b in stuff[4]:
            print(b)
        print('Merged breakdown output can be found in')
        print(one)
        print(two)
    return retme

def scan_for_abs_frac(infiles,outfile,njobs):
    abspart,fracpart='',''
    for f in infiles:
        buff=open(f,'r').read().split('*\n')
        abspart +=buff[0].replace(f'_job0of{njobs}','')
        fracpart+=buff[1]
    donau=open(outfile,'w')
    donau.write(abspart)
    donau.write(fracpart)
    donau.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Breakdown merging')
    parser.add_argument('workspace',help='The name of your workspace including an appropriately placed _job*of[NJOBS]_ string')
    parser.add_argument('-d','--directory',help='Top direcotry in which to look for the breakdown files',default='.')
    parser.add_argument('-m','--mode',help='Breakdown mode (in case you run multiple modes and need to specify; the default will act as if there is only one)',default=-1)
    parser.add_argument('-a','--asimov',help='Asimov setting for the breakdown (in case you run multiple modes and need to specify; the default will act as if there is only one)',default=-1)
    args=parser.parse_args()

    fetch_and_merge(args.directory,args.workspace,args.mode,args.asimov)
