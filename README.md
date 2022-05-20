# 💡ModelFarm

An open-source python library to train deep learning models on Amazon EC2 Spot Instances (regular EC2 instances are also supported).  
The short-term goals are:
- Provide an easy way to launch a GPU-enabled EC2 instance, run a training script and extract artifacts
- Provide convenience classes to run common jobs (eg. TimmJob, DetectronJob) so that only the train arguments still have to be provided
- Provide a ModelFarm class which:
    - Takes a dataset, a job class and a budget of GPU minutes
    - Preprocesses the dataset if needed and puts it on S3
    - Launches training jobs with a prespecified concurrency
    - In a first phase the jobs will be a predefined list of logical trials, eg. try a resnet50 and an efficientnet.  In a second phase an AutoML approach could be used.
    - All job artifacts are collected from the machines
    - Once the budget is spent, information on the best model is returned.  