import random
from queue import Queue, PriorityQueue
import matplotlib.pyplot as plt
import numpy as np
import datetime
import math
from scipy import stats
import pandas as pd
import PEVC.models as PM
import config.param as CP
import PEVC.utils as PU
import json
import zipfile

random.seed(1)

cfg = CP.Settings()
print(cfg.sim_time)

ev_data, total_elec_price, ev_share = PU.get_data(cfg)
charger_modes = PU.get_modes(cfg)
total_load = PU.get_load(cfg)

scenarios = pd.DataFrame()

scenario = 1

for park_slot in cfg.parking_slots:
    # Number of Parkings
    # Get charger modes
    for charger_mode in charger_modes:

        print(f"Scenario {scenario} - No. Chargers {len(charger_mode)} / No. Park Slots {park_slot}")
        num_chargers = len(charger_mode)

        # Add chargers to the station

        _id = 0

        scenario += 1
        
        PEVC_station = PM.Station()
        
        for charger_level in charger_mode:
            _id += 1
            PEVC_station.add(PM.Charger(level=charger_level, queue_size=park_slot, charger_type=charger_level, charger_mode=charger_mode, charger_id=_id))
            
        PEVC_station.ready()
                
        time = 0
        initial = time
        Sim_time = 1440*cfg.sim_time
        
        rand_choice = np.random.randint(0, len(PEVC_station.chargers))
        PEVC_station.chargers[rand_choice].line.put((time, "Arrival"))
        
        while time < Sim_time:
            for plug in range(len(PEVC_station.chargers)):
                if len(PEVC_station.chargers[plug].line.queue):
                    (time, event_type) = PEVC_station.chargers[plug].line.get()
                    if event_type == "Arrival":
                        car_brand = PU.get_car(ev_share)
                        ev = PM.EV(time, ev_models=ev_data, car_brand=car_brand)
                        PM.Arrival(time, PEVC_station.chargers[plug], PEVC_station.chargers, total_load, ev)
                    elif event_type == "Departure from Charger":
                        PM.Departure(time, PEVC_station.chargers[plug], PEVC_station.chargers)

        temp = pd.DataFrame(data=[PEVC_station])
        scenarios = pd.concat([scenarios, temp]).reset_index().drop(columns=['index'])


final_results = PU.prepare_results(total_elec_price, scenarios, cfg)

if cfg.save_df:
    final_results.to_csv(f'Simulation_results.csv')

if cfg.print_df:
    print(final_results)