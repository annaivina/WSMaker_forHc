import subprocess as sp
import time, os, uuid, glob, re, stat
import networkx as nx

class JobUtils:

    @staticmethod
    def write_job_preamble(jobfile):
        jobfile.write("""#!/bin/bash
export X509_USER_PROXY={proxy_cert_location}
unset DISPLAY
cd {anadir}
source ./setup.sh &> /dev/null
""".format(anadir = os.getenv("ANALYSISDIR"), proxy_cert_location = os.getenv("X509_USER_PROXY")))

class Task:

    def __init__(self, taskname, job_generator, prerequisites = []):
        
        self.taskname = taskname
        self.job_generator = job_generator
        self.prerequisites = prerequisites
        self.jobs = None # they don't exist yet, but get created when this task is scheduled

    def generate_jobs(self):

        if self.jobs is None:
            self.jobs = self.job_generator()

        return self.jobs

    def can_start(self, tasks):
        return set(self.prerequisites).issubset(set(tasks))

class AtomicTask(Task):

    # a task that does the work of a WSMakerJob
    def __init__(self, name, commands, submit_dir, log_dir, prerequisites, settings):

        def job_generator():
            return [WSMakerJob(name, commands, submit_dir, log_dir, prerequisites = [], settings = settings)]

        super().__init__(taskname = name, job_generator = job_generator, prerequisites = prerequisites)

class Scheduler:

    @staticmethod
    def schedule(tasks, submit_task, task_completed, scheduling_finished, max_concurrent_jobs = -1):

        def update_task_status(tasks_scheduled, tasks_to_run, tasks_running, tasks_completed):
            # scheduled -> running
            for task in tasks_scheduled:
                tasks_running.append(task)
                tasks_to_run.remove(task)

            # running -> completed
            for task in tasks_running:
                if task_completed(task):
                    tasks_running.remove(task)
                    tasks_completed.append(task)

        # build the graph of tasks
        task_dag = nx.DiGraph()
        task_dag.add_nodes_from(tasks)
        
        for task in tasks:
            for prerequisite in task.prerequisites:
                task_dag.add_edge(prerequisite, task)

        # traverse the graph in the order of the dependencies and start all the tasks
        # that can be started
        tasks_running = []
        tasks_completed = []
        tasks_to_run = [task for task in nx.topological_sort(task_dag)]

        while not scheduling_finished(tasks_to_run, tasks_running):

            # start all tasks that can be started
            tasks_scheduled = []

            for task in tasks_to_run:
                if task.can_start(tasks_completed) and (len(tasks_scheduled) + len(tasks_running) < max_concurrent_jobs or max_concurrent_jobs < 0):
                    tasks_scheduled.append(task)

            for task in tasks_scheduled:
                submit_task(task)

            # update the books
            update_task_status(tasks_scheduled, tasks_to_run, tasks_running, tasks_completed)
            time.sleep(5)

class TaskScheduler(Scheduler):

    @staticmethod
    def schedule(tasks, jobSubmitter):

        def submit_task(task):
            print(f"started task {task.taskname}")
            jobSubmitter.submit(task.generate_jobs(), dagname = task.taskname)

        def task_completed(task):
            # the task is complete as soon as all of its jobs are
            return all([jobSubmitter.is_complete(job) for job in task.generate_jobs()])

        def scheduling_finished(tasks_to_run, tasks_running):
            # return as soon as no more tasks need to be scheduled
            return len(tasks_to_run) == 0

        super(TaskScheduler, TaskScheduler).schedule(tasks, submit_task, task_completed, scheduling_finished)

class Job:

    def __init__(self, jobname, executable_generator, prerequisites = [], settings = None):

        # make sure to put things into a list, even if
        # only a single prerequisite is passed
        if not isinstance(prerequisites, list):
            prerequisites = [prerequisites]

        # the name of the job
        self.jobname = jobname

        # other jobs that are prerequisites of this one (i.e. that 
        # need to be completed for this one to be able to start)
        self.prerequisites = prerequisites

        # returns the path to the executable that runs this job
        self.executable_generator = executable_generator

        # additional options relevant for the submission of this job
        self.settings = settings

    def generate_executable(self):
        return self.executable_generator()

    def get_parents(self, jobs):
        return self.prerequisites

    def can_start(self, jobs):
        return set(self.prerequisites).issubset(set(jobs))

class WSMakerJob(Job):

    def __init__(self, name, commands, submit_dir, log_dir, prerequisites, settings):

        if not isinstance(commands, list):
            commands = [commands]

        def executable_generator():
            
            jobpath = os.path.join(submit_dir, name + ".sh")

            with open(jobpath, 'w') as jobfile:
                JobUtils.write_job_preamble(jobfile)

                for cmd_ind, command in enumerate(commands):

                    if len(commands) > 1:
                        logfile_path = os.path.join(log_dir, f"{name}_cmd_{cmd_ind}.log")
                    else:
                        logfile_path = os.path.join(log_dir, name + ".log")

                    redirect_output = f" > {logfile_path} 2>&1"

                    jobfile.write(command + redirect_output + '\n')

            return jobpath

        super().__init__(jobname = name, executable_generator = executable_generator,
                                         prerequisites = prerequisites, settings = settings)

class TorqueJobSubmitter:

    @staticmethod
    def submit(jobs, dagname = None):

        #if there is nothing to submit, give up 
        if not jobs:
            return

        #match job IDs to job names
        d_id_name = {}

        # job graph is handy because we need to submit jobs with dependencies for which we know the job ID first
        job_dag = nx.DiGraph()
        job_dag.add_nodes_from(jobs)
        
        for job in jobs:
            for prerequisite in job.prerequisites:
                job_dag.add_edge(prerequisite, job)
        
        # traverse the graph in the order of the dependencies
        for job in nx.topological_sort(job_dag):
            #generate the possible job dependences
            depstr = ""
            parents = job.get_parents(jobs)
            if len(parents) > 0:
                depstr += "depend=afterok"
                for parent_job in parents:
                    depstr += ":"+parent_job.cluster_id
            
            #job options
            add_opt = f"nodes=1:ppn={job.settings.number_CPUs}"
            #nikhef torque doesn't allow runtime selection --> convert to queue
            queue = "short"
            rt = job.settings.runtime
            if rt > 14400:
                queue = "generic"
            job.queue = queue
            #job submission
            exec_path = job.generate_executable()
            if not depstr:
                pid = sp.check_output(["qsub", "-q", queue, "-l", add_opt,  exec_path])
            else:
                pid = sp.check_output(["qsub", "-q", queue, "-l", add_opt, "-W", depstr, exec_path])
            job.cluster_id = pid.replace('\n','') #this replace might be nikhef specific but shouldn't hurt

    @staticmethod
    def is_complete(job):
        # check whether this job is still running
        reply = sp.check_output(["qstat", str(job.cluster_id)])
        status_pattern = r".*\ ([A-Z])\ "+job.queue
        status = re.search(status_pattern, reply).group(1)
        if status == "C":
            return True
        else:
            return False


class CondorJobSubmitter:
    
    @staticmethod
    def submit(jobs, dagname = None):

        # if there is nothing to submit, give up immediately
        if not jobs:
            return

        if not dagname:
            dagname = str(uuid.uuid4())

        def build_condor_submit_file(executable, path, settings):
            
            st = os.stat(executable)
            os.chmod(executable, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            with open(path, 'w') as submit_file:
                submit_file.write(f"executable = {executable}\n")

                # if there are additional requirements that need to be met,
                # specify them in the submit file
                if settings:
                    submit_file.write(f"request_cpus = {settings.number_CPUs}\n")
                    submit_file.write(f"request_memory = {settings.memory}\n")
                    submit_file.write(f"+MaxRuntime = {settings.runtime}\n")

                submit_file.write("queue\n")
        
        def extract_cluster_id(reply):
            reply = str(reply.replace(b'\n', b' '), 'UTF-8') # avoid regex subtleties if string contains linebreaks
            cluster_id_finder = re.compile(".*submitted to cluster (.+?)\\s+")
            match = cluster_id_finder.match(reply)
            if match:
                return int(float(match.group(1)))
            else:
                raise RuntimeError("Error: submission of DAG to Condor encountered problems")
                
        # prepare the submit files for each individual job
        for job in jobs:
            exec_path = job.generate_executable()
            submit_dir = os.path.dirname(exec_path)
            job.submitpath = os.path.join(submit_dir, os.path.splitext(os.path.basename(exec_path))[0] + ".sub")
            build_condor_submit_file(executable = exec_path, path = job.submitpath, settings = job.settings)

        # prepare the dagfile
        dagpath = os.path.join(submit_dir, dagname + ".dag")
        with open(dagpath, 'w') as dagfile:

            # define the jobs
            for job in jobs:
                dagfile.write(f"JOB {job.jobname} {job.submitpath}\n")

            # define the dependencies
            for job in jobs:
                parents = job.get_parents(jobs)

                if len(parents) > 0:
                    parents_names = [cur.jobname for cur in parents]
                else:
                    continue
                
                dagfile.write("PARENT {parents} CHILD {children}\n".format(parents = " ".join(parents_names), children = job.jobname))

        # ready to submit!
        while True:
            try:
                reply = sp.check_output(["condor_submit_dag", "-force", "-batch-name", dagname, dagpath])
                break
            except:
                print("Problem submitting job - retrying in 10 seconds!") 
                time.sleep(10)

        # extract the cluster ID and keep it
        cluster_id = extract_cluster_id(reply)

        for job in jobs:
            job.cluster_id = cluster_id

    @staticmethod
    def is_complete(job):
        # check whether this job is still running
        while True:
            try:
                reply = sp.check_output(["condor_q", "-long", "-attributes", "ClusterId", str(job.cluster_id)])
                break
            except:
                print("Problem retrieving job status - retrying in 10 seconds!") 
                time.sleep(10)
                
        if len(reply) > 0:
            return False
        else:
            return True

class LocalJobSubmitter(Scheduler):

    @staticmethod
    def is_complete(job):
        if job.pid.poll() is not None:
            return True  
        else:
            return False

    @staticmethod
    def submit(jobs, max_concurrent_jobs = 4, dagname = None):

        def submit_job(job):
            pid = sp.Popen(["bash", job.generate_executable()])
            job.pid = pid
            print(f"started job {job.jobname}")

        def scheduling_finished(tasks_to_run, tasks_running):
            # return when nothing more needs to be done
            return len(tasks_to_run) == 0 and len(tasks_running) == 0

        super(LocalJobSubmitter, LocalJobSubmitter).schedule(jobs, submit_job, LocalJobSubmitter.is_complete, scheduling_finished, max_concurrent_jobs = max_concurrent_jobs)

# ----------------------------------------------------------------------
# some convenience methods that expose the same interface as before
# ----------------------------------------------------------------------
def run_batch(configs, outversion, algs, driver = "local"):
    outdir = "output"
    try:
        os.mkdir(outdir)
    except OSError:
        pass
        
    for config in configs:
        print(f"launching job for config {config}")
        cmd = create_python_command(config, outversion, algs, driver = driver)
        print(" ".join(cmd))
        master_job = sp.Popen(cmd)
        master_job.communicate()
        print("done")

def run_local_batch(configs, outversion, algs):
    return run_batch(configs, outversion, algs, driver = "local")

def run_condor_batch(configs, outversion, algs):
    return run_batch(configs, outversion, algs, driver = "condor")

def run_torque_batch(configs, outversion, algs):
    return run_batch(configs, outversion, algs, driver = "torque")

def run_lxplus_batch(configs, outversion, algs):
    return run_batch(configs, outversion, algs, driver = "condor")

def get_ws_name(conf, outver):
    import subprocess
    suff = "_" + os.path.splitext(os.path.basename(conf))[0]
    outversion = outver + suff
    cutver = subprocess.getoutput(f"grep \"InputVersion \" {conf} | awk -F ' ' '{{print $2}}'").lstrip(' \t')
    return cutver, outversion    

def config_to_dict(conf_file):
    with open(conf_file) as f:
        return dict(l.split() for l in f if not l.isspace() and len(l.split())==2)

def create_python_command(conf_file, outversion, algs, **kwargs):
    command = ["python", "WSMakerCore/scripts/doActions.py"]
    conf_dict = config_to_dict(conf_file)

    # add optional arguments
    for alg in algs:
        command.append(alg.format(**conf_dict))

    for arg, val in list(kwargs.items()):
        command += ["--" + arg, val]

    # add positional arguments
    command.append(conf_file)
    command.append(outversion)

    return command
