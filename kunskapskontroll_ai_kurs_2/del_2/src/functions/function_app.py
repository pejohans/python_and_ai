
import os
import json
import logging
import datetime

import azure.functions as func
import pandas as pd

#from stockml_pipeline.pipeline import run_nightly_pipeline

app = func.FunctionApp()

# Schedule uses NCRONTAB (6 fields). Example: 0 0 1 * * * = 01:00 UTC daily
TIMER_SCHEDULE = os.getenv("TIMER_SCHEDULE", "0 0 1 * * *")

@app.function_name(name="nightly_stockml_pipeline")
@app.schedule(schedule=TIMER_SCHEDULE, arg_name="mytimer", run_on_startup=False, use_monitor=True)
def nightly_stockml_pipeline(mytimer: func.TimerRequest) -> None:
    if mytimer.past_due:
        logging.warning('Timer is past due!')

    run_date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    horizon_days = int(os.getenv("HORIZON_DAYS", "7"))

    logging.info(f"Starting nightly pipeline. date={run_date} horizon={horizon_days}")
    #run_nightly_pipeline(run_date=run_date, horizon_days=horizon_days)
    logging.info("Nightly pipeline completed")
