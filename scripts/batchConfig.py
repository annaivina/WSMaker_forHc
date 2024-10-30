class metaBatchConfig(type):
    """
    metaBatchConfig enables that 
    each child class inheriting from BatchConfig will inherit also its members and functions 
    see: https://stackoverflow.com/a/50819088/8390668

    First parent class __init__ function are called 
    then the child class __init__ 
    so that the user can override variables in child classes 
    """
    def __init__(cls,name,bases,dct):
        def auto__call__init__(self, *a, **kw):
            for base in cls.__bases__:
                base.__init__(self, *a, **kw)
            cls.__init__child_(self, *a, **kw)
        cls.__init__child_ = cls.__init__
        cls.__init__ = auto__call__init__

class BatchConfig(metaclass=metaBatchConfig):
    """
    Analyses can define a class derived from this one to fine-tune the settings
    to their needs.
    In case of derived class no need to add the metaclass
    see: https://stackoverflow.com/a/50819088/8390668
    """
    class JobSettings:

        def __init__(self, number_CPUs = 1, memory = "1 GB", runtime = 3600):
            self.number_CPUs = number_CPUs # number of CPUs to request on the worker node
            self.memory = memory # amount of RAM to request, e.g. "10 GB"
            self.runtime = runtime # max. runtime (in seconds) to request
            
    def __init__(self):

        self.default_settings = BatchConfig.JobSettings() # this is the baseline for all jobs
    
        # ----------------------------------
        # for NP ranking
        # ----------------------------------
        # NB: ranking_job_settings is soon to be deprecated and removed 
        # Use instead the more general method 
        # self.setJobSettings("RankingTask",BatchConfig.JobSettings(number_CPUs = 1,runtime=4*3600)) 
        self.ranking_job_settings = BatchConfig.JobSettings(number_CPUs = 1)
        self.number_ranking_jobs = 10

        # ----------------------------------
        # for breakdown
        # ----------------------------------
        self.categories_per_breakdown_job = -1 #-1: all

        # dictionnary of job settings defined by the user (one setting per task)
        self._dict_jobSettings = {}

    def setJobSettings(self,taskName,jobSettings): 
        """
        User can define specific job settings per task 
        in its custom BatchConfig class (see also doActions.py) 
        e.g.
            self.setJobSettings("RankingTask", BatchConfig.JobSettings(number_CPUs = 1,runtime=4*3600))
            self.setJobSettings("LimitTask", BatchConfig.JobSettings(runtime=3*3600))
            self.setJobSettings("BreakdownTask", BatchConfig.JobSettings(runtime=5*3600,memory = "2 GB"))
        """
        if taskName not in self._dict_jobSettings: 
            self._dict_jobSettings[taskName] = jobSettings
        else: 
            # prevent changing jobs settings 
            raise RuntimeError("Already set job settings for taskName".format(taskName))

    def getJobSettings(self,taskName): 
        if taskName in self._dict_jobSettings:
            # return user define settings 
            return self._dict_jobSettings[taskName]
        else: 
            if taskName == "RankingTask": 
                # in case the user ask for ranking task and did not use the new setJobSettings method 
                # return the ranking job settings (which can be defined by the user)
                return self.ranking_job_settings 
            else: 
                # no user defined settings for that task
                # return default settings in that case 
                return self.default_settings