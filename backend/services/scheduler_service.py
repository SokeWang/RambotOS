import os
import importlib.util
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tasks")
        os.makedirs(self.tasks_dir, exist_ok=True)
        self.jobs = {}

    def start(self):
        self.scheduler.start()
        self.load_all_tasks()
        logger.info("SchedulerService started.")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("SchedulerService shut down.")

    def load_all_tasks(self):
        if not os.path.exists(self.tasks_dir):
            return
        for f in os.listdir(self.tasks_dir):
            if f.endswith(".py") and not f.startswith("__"):
                self.load_task(f)

    def load_task(self, filename):
        task_name = filename[:-3]
        filepath = os.path.join(self.tasks_dir, filename)
        try:
            spec = importlib.util.spec_from_file_location(task_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'execute') and hasattr(module, 'TRIGGER_ARGS'):
                trigger_args = module.TRIGGER_ARGS.copy()
                trigger = trigger_args.pop("trigger", "cron")
                
                async def execute_wrapper():
                    try:
                        logger.info(f"Task Scheduler: Executing {task_name}")
                        await module.execute()
                    except Exception as e:
                        logger.error(f"Task Scheduler Error in {task_name}: {e}")

                if task_name in self.jobs:
                    self.scheduler.remove_job(self.jobs[task_name])
                
                job = self.scheduler.add_job(execute_wrapper, trigger, id=task_name, replace_existing=True, **trigger_args)
                self.jobs[task_name] = job.id
                logger.info(f"Loaded scheduled task: {task_name} with args: {trigger_args}")
            else:
                logger.warning(f"Task module {filename} missing 'execute' or 'TRIGGER_ARGS'")
        except Exception as e:
            logger.error(f"Failed to load task {filename}: {e}")

    def get_status_dict(self):
        # Used by core to inject into the monitors UI
        status_dict = {}
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                sublabel = f"Next Run: {next_run.strftime('%Y-%m-%d %H:%M')}"
                status = "running"
            else:
                sublabel = "Paused"
                status = "stopped"
                
            status_dict[job.id] = {
                "name": job.id,
                "status": status,
                "pid": None,
                "last_ping": 0,
                "uptime": 0,
                "label": job.id.replace("_", " ").title(),
                "sublabel": sublabel,
                "icon": "Clock",
                "color": "purple"
            }
        return status_dict

    def toggle_task(self, name, enable):
        job = self.scheduler.get_job(name)
        if job:
            if enable:
                job.resume()
                logger.info(f"SchedulerService: Resumed job {name}")
            else:
                job.pause()
                logger.info(f"SchedulerService: Paused job {name}")
            return True
        return False

scheduler_service = SchedulerService()
