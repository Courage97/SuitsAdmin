from django_cron import CronJobBase, Schedule
from .utils import fetch_live_exchange_rates

class UpdateExchangeRatesCronJob(CronJobBase):
    RUN_EVERY_MINS = 1440  # Run once per day

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "billing.update_exchange_rates"  # Unique identifier

    def do(self):
        fetch_live_exchange_rates()
