
import random
from queue import Queue, PriorityQueue
import numpy as np
import pandas as pd

class Charger(object):
    
    def __init__(self, level, queue_size, charger_type, charger_mode, charger_id):
        
        # General charger Information
        
        self.charger_mode = charger_mode
        self.charger_id = charger_id
        self.line = PriorityQueue()
        self.users = 0
        self.in_service = 0
        self.delayed = []
        self.temp_st = []
        self.count = 0
        self.queue = []
        self.loss = 0
        self.loss_list = []
        self.st_w = 0
        self.bt = 0
        self.st = 0
        
        self.charger_type = charger_type
        self.queue_size = queue_size
        
        if self.charger_type=="Level B":
            self.max_charge_speed = 43 # KW/H
        elif self.charger_type=="Level C":
            self.max_charge_speed = 350 # KW/H
        
        # charger Measurements
        self.n_arrival = 0
        self.n_departure = 0
        self.old_time = 0
        self.utq = 0
        self.ut = 0
        self.delay = 0
        self.delays = []
        self.consumers = []

class Station(object):
    
    def __init__(self):
        self.main_line = PriorityQueue()
        self.chargers = []
        self.n_chargers = 0
        
    def add(self, charger):
        self.chargers.append(charger)
        
    def ready(self):
        self.bt_status = np.zeros(len(self.chargers))

class EV(object):
    
    def __init__(self, arrival_time, ev_models, car_brand):
        self.car = ev_models[ev_models['Brand'] == car_brand].sample(1)
        self.brand = self.car['Brand']
        self.model = self.car['Model']
        self.battery_cap = self.car['Battery_Pack Kwh']
        self.charge_speed = self.car['FastCharge_Speed Kw/H']
        self.range_km = self.car['Range_Km']
        self.arrival_time = arrival_time
        self.current_charge = (round(random.uniform(5, 30),2)/100)*self.battery_cap
        self.desired_charge = (round(random.uniform(80, 100),2)/100)*self.battery_cap
        self.charge_need = self.desired_charge - self.current_charge
        self.max_charge_time = (self.charge_need/self.charge_speed)*60
        self.dist_to_next = (self.current_charge*self.range_km)/self.battery_cap

def Arrival(time, charger, chargers, total_load, ev):
        
    charger.n_arrival += 1
    charger.utq += ((charger.users) - (charger.in_service)) * (time - charger.old_time)
    charger.ut += (charger.users)*(time - charger.old_time)
    charger.old_time = time
    
    condition = []
    list_res = (list(set(charger.charger_mode)))
    choice = random.choice(list_res)
    for p in chargers:
        if p.charger_type==choice:
            condition.append((p.charger_type, p.bt, p.charger_id))
    charger_to_go = min(condition, key=lambda val: val[1])[2]-1
        
    LOAD = round(total_load[round(time)], 2)
    SERVICE = 340 #charger.max_charge_speed # Average Service Time
    ARRIVAL = SERVICE/LOAD # Average Interarrival Time
    inter_arrival = random.expovariate(lambd=1.0/ARRIVAL)
    chargers[charger_to_go].line.put((time + inter_arrival, "Arrival"))
    
    if (len(charger.queue) < (charger.queue_size)):
        
        #print(f"ARR Charger {str(charger.charger_id)} - ({charger.charger_type}): Arrival No. ({charger.n_arrival}) at time {time} with {charger.users} users in queue!")      
        charger.users += 1
        charger.queue.append(ev)
        charger.delayed.append(ev.arrival_time)
        
        if charger.users==1:
            
            charger.delayed.remove(ev.arrival_time)
            charger.count += 1
            service_time = (ev.charge_need/min(ev.charge_speed.iloc[0], charger.max_charge_speed)).iloc[0]*60
            charger.line.put((time + service_time, "Departure from Charger"))
            charger.st += service_time
            charger.consumers.append((time, service_time/60, ev.charge_need.iloc[0]))
            charger.bt = time + service_time
            charger.in_service += 1
            
    else:
        charger.loss += 1
        charger.loss_list.append(ev)
        #print(f"B-ARR Charger {str(charger.charger_id)} - ({charger.charger_type}): Bypassed Arrival No. ({charger.n_arrival}) at time {time} with {charger.users} users in queue!")
    

def Departure(time, charger, chargers):
    global in_service
    global busy_time       
            
    if len(charger.queue) != 0 :
    # Get the first element from the queue
        ev = charger.queue.pop(0)
        #print(f"DEP Charger {str(charger.charger_id)} - ({charger.charger_type}): Departure No. ({charger.n_departure+1}) at time {time} with {charger.users-1} users in queue!")
        charger.delay += (time-ev.arrival_time)
        charger.delays.append(time-ev.arrival_time)
        charger.n_departure += 1
        charger.ut += (charger.users)*(time - charger.old_time)
        charger.utq += ((charger.users) - (charger.in_service)) * (time - charger.old_time)
        charger.old_time = time
        charger.in_service -= 1
        charger.users -= 1

    # See whether there are more clients to in the line

        if charger.users > 0:
            ev = charger.queue[0]
            service_time = (ev.charge_need/min(ev.charge_speed.iloc[0], charger.max_charge_speed)).iloc[0]*60
            charger.line.put((time + service_time, "Departure from Charger"))
            charger.st += service_time
            charger.consumers.append((time, service_time/60, ev.charge_need.iloc[0]))
            charger.bt = time + service_time
            charger.in_service += 1