import random
from model import EV

def time_converter(time, mode='print'):
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)
    if mode=='print':
        return str("%d:%02d:%02d" % (hours, minutes, seconds))
    if mode=='num':
        return hours, minutes, seconds

def arrival(time, plug, station, kw_charge, inter_arrival):
    global in_service
    global n_plug
            
    
    data.arr += 1
    data.oldT = time
    plug.n_arrival += 1
    plug.utq += ((plug.users) - (plug.in_service)) * (time - plug.oTime)
    plug.ut += (plug.users)*(time - plug.oTime)
    plug.oTime = time
    
    # Getting Random Choice for Each Drone
    rand_choice = random.randint(0, len(station)-1)
    while station[rand_choice].status!="Online":
        rand_choice = random.randint(0, len(station)-1)
    station[rand_choice].FES.put((time + inter_arrival, "Arrival"))

    # Getting requested EV information
    ev = EV(TYPE1, time)
    
    if (len(plug.queue) < (plug.buffersize)) and (plug.service_condition == "At Service"):
        print(f"ARR plug {str(plug.nQ)} - {plug.name} {plug.status} ({plug.charge_level}): Arrival No. {data.arr} ({plug.n_arrival}) at time {time_converter(time, mode='print')} with {plug.users} users in queue!")      
        plug.users += 1
        data.users += 1
        plug.queue.append(ev)
        plug.delayed.append(ev.arrival_time)
        
        if plug.users==1:
            plug.delayed.remove(ev.arrival_time)
            plug.count += 1
            plug.FES.put((time + kw_charge, "Departure from Server"))
            plug.charge_consume(kw_charge)
            plug.in_service += 1
            data.in_service += 1
        
    else:
        plug.loss += 1
        if plug.status=="In Charge":
            plug.loss_outofactivity += 1
        print(f"B-ARR plug {str(plug.nQ)} - {plug.name} {plug.status} ({plug.charge_level}): Bypassed Arrival No. {data.arr} ({plug.n_arrival}) at time {time_converter(time, mode='print')} with {plug.users} users in queue!")

def departure(time, plug, station, kw_charge):
    global delay 
    global in_service
    global busy_time       


    # For those who experienced delay [Waiting line]
    if plug.status=="In Charge":
        while plug.users>0:
            print(f"B-DEP plug {str(station[i].nQ)} - {station[i].name} {station[i].status} ({station[i].charge_level}): Departure Canceled at time {time_converter(time, mode='print')} with {station[i].users-1} users in queue!")
            ev = plug.queue.pop(0) 
            station[i].in_service -= 1
            station[i].users -= 1
            data.users -= 1
            station[i].loss += 1
            station[i].loss_outofactivity += 1
            
    
    else:
        if len(plug.queue) != 0 :
        # Get the first element from the queue
            ev = plug.queue.pop(0)
            print(f"DEP plug {str(plug.nQ)} - {plug.name} {plug.status} ({plug.charge_level}): Departure No. {data.dep+1} ({plug.n_departure+1}) at time {time_converter(time, mode='print')} with {plug.users-1} users in queue!")
            plug.delay += (time-ev.arrival_time)
            data.delay += (time-ev.arrival_time)
            plug.delays.append(time-ev.arrival_time)
            data.delays.append(time-ev.arrival_time)
            data.dep += 1
            data.oldT = time
            plug.n_departure += 1
            plug.ut += (plug.users)*(time - plug.oTime)
            plug.utq += ((plug.users) - (plug.in_service)) * (time - plug.oTime)
            plug.oTime = time
            plug.in_service -= 1
            plug.users -= 1

        # See whether there are more evs to in the line

            if plug.users > 0:   
                plug.st += kw_charge
                data.st += kw_charge
                plug.FES.put((time + kw_charge, "Departure from Server"))
                plug.charge_consume(kw_charge)
                delay.append(time - ev.arrival_time)
                busy_time += kw_charge 
                plug.in_service += 1
                data.in_service += 1