from batchConfig import BatchConfig as bcfg

class BatchConfig(bcfg):

    def __init__(self):
        # runtime in seconds
        self.default_settings = BatchConfig.JobSettings(number_CPUs = 1,runtime = 24*3600, memory = 12*1024) # this is the baseline for jobs if no particular settings is defined for the task in question 

        # For task names see WSMakerCore/scripts/doActions.py 
        # build is quick 
        self.setJobSettings("BuildWorkspaceTask"   , BatchConfig.JobSettings(number_CPUs = 1, runtime = 1*3600))
        # ----------------------------------
        # for NP ranking
        # ----------------------------------
        # Ranking is slow 
        self.setJobSettings("RankingTask" , BatchConfig.JobSettings(number_CPUs = 1, runtime = 3*3600))
        self.number_ranking_jobs = 200

        # Breakdown is slow 
        # ----------------------------------
        # for breakdown
        # ----------------------------------
        self.categories_per_breakdown_job = 1 #-1: all
        # longest task ask for 1 day to make sure the jobs have time to complete 
        self.setJobSettings("BreakdownTask"   , BatchConfig.JobSettings(number_CPUs = 1, runtime = 24*3600))

        # Other tasks 
        # (not all of them are listed, the rest of the task get the baseline default settings)
        # request more memory for FCC, Limit and Significance tasks to avoid it getting sent to HOLD
        self.setJobSettings("FCCTask"         , BatchConfig.JobSettings(number_CPUs = 1, runtime = 2*3600, memory = 8*1024))
        self.setJobSettings("LimitTask"       , BatchConfig.JobSettings(number_CPUs = 1, runtime = 2*3600, memory = 12*1024))
        # ranking plot and significance task are quick 
        self.setJobSettings("RankingPlotTask" , BatchConfig.JobSettings(number_CPUs = 1, runtime = 1*3600))
        self.setJobSettings("SignificanceTask", BatchConfig.JobSettings(number_CPUs = 1, runtime = 1*3600, memory = 8*1024))

