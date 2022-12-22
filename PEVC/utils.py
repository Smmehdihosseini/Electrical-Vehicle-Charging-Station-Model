
import zipfile
import numpy as np
import pandas as pd
import json
import random
import math
from scipy import stats

def get_car(ev_share):
    
    ev_prob_sum = sum(ev_share.values())
    for key in ev_share:
        ev_share[key] = ev_share[key]/ev_prob_sum

    return list(ev_share.keys())[np.random.choice(len(ev_share.keys()), 1,
                                      replace = False,
                                      p=list(ev_share.values()))[0]]

def get_data(cfg):

    ev_data = pd.read_csv("PEVC/src/ev_desc_data.csv")

    evs = ev_data.drop(columns=['Segment', 'Seats', 'PriceEuro', 'PowerTrain', 'TopSpeed_KmH',
                                      'AccelSec', 'BodyStyle', 'RapidCharge'])
    evs = evs.rename(columns={'Efficiency_WhKm':'Efficiency_KWh/100Km'})
    evs['Efficiency_KWh/100Km'] = evs['Efficiency_KWh/100Km']/10
    evs['FastCharge_Speed Kw/H'] = (60*evs['Battery_Pack Kwh'])/((evs['Range_Km']/evs['FastCharge_KmH'])*60)

    zf = zipfile.ZipFile('PEVC/src/european_electricity_price_data_hourly.zip') 
    elec_price = pd.read_csv(zf.open('european_electricity_price_data_hourly.csv'))
    elec_price_city = cfg.sim_region
    elec_price_unique = elec_price[elec_price['Country']==elec_price_city].drop(columns=['Country', 'ISO3 Code', 'Datetime (Local)'])
    elec_price_unique = elec_price_unique.rename(columns={'Price (EUR/MWhe)':'Price (EUR/KWhe)'}).set_index('Datetime (UTC)')
    elec_price_unique['Price (EUR/KWhe)'] = elec_price_unique['Price (EUR/KWhe)'].div(1000)

    with open('PEVC/src/ev_market.json') as json_file:
        ev_share = json.load(json_file)

    return evs, elec_price_unique[-1*(cfg.sim_time+1)*24:], ev_share

def get_load(cfg):

    total_load = np.array([])
    for day in range(0, cfg.sim_time+1):
        load_data = np.linspace(0, 1450, 1450)
        first_peak = np.random.randint(min(cfg.first_peak_range), max(cfg.first_peak_range))
        second_peak = np.random.randint(min(cfg.second_peak_range), max(cfg.second_peak_range))
        P1, P2 = first_peak*60, second_peak*60
        S = math.sqrt(1450)
        max_load_factor = random.uniform(4.8, 5.5)
        daily_load = (stats.norm.pdf(load_data, P1, 15*S)+ stats.norm.pdf(load_data, P2, 15*S))*max_load_factor*1000 + cfg.min_traff_load + cfg.min_traff_load
        total_load = np.concatenate((total_load, daily_load), axis=None)

    return total_load

def get_modes(cfg):

    all_modes = []
    for m in cfg.charger_modes:
        _mode = []
        for b in range(m[0]):
            _mode.append('Level B')
        for c in range(m[1]):
            _mode.append('Level C')
        all_modes.append(_mode)

    return all_modes

def prepare_results(elec_price, obj_results, cfg):

    headers = ['mode', 'qsize', 'loss', 'arr', 'dep', 'st', 'ut', 'utq', 'delay', 'delayed',
               'ch_time', 'stay_time', 'power', 'bought', 'profit', 'park_fee']

    simulate = []

    for i in range(0, obj_results.shape[0]):
        print(f"Preparing Data for Scenario {i}")
        sc = obj_results.iloc[i][0]
        _mode = sc.chargers[0].charger_mode
        _qsize = sc.chargers[0].queue_size
        _loss = 0
        _arrivals = 0
        _departures = 0
        _st = 0
        _ut = 0
        _utq = 0
        _delay = 0
        _delayed = 0
        _ch_time = 0
        _stay_time =0
        _power = 0
        _bought_power = 0
        _profit = 0
        _park_fee = 0

        for charger in sc.chargers:
            _loss += charger.loss
            _arrivals += charger.n_arrival/len(sc.chargers)
            _departures += charger.n_departure/len(sc.chargers)
            _st += charger.st/len(sc.chargers)
            _ut += charger.ut/len(sc.chargers)
            _utq += charger.utq/len(sc.chargers)
            _delay += charger.delay/len(sc.chargers)
            _delayed += len(charger.delayed)/len(sc.chargers)
            for con in charger.consumers:
                _ch_time += con[0]
                _stay_time += con[1]
                _power += con[2]
                _bought_power += con[2]*elec_price.iloc[int(round(con[0])/60)][0]
                if charger.charger_type=='Level B':
                    _profit += con[2]*elec_price.iloc[int(round(con[0])/60)][0]
                else:
                    _profit += 8*con[2]*elec_price.iloc[int(round(con[0])/60)][0]
                _park_fee += con[1]*cfg.parking_fee
            
        temp = [_mode, _qsize, _loss, _arrivals, _departures, _st,
                _ut, _utq, _delay, _delayed, _ch_time, _stay_time, _power, _bought_power, _profit, _park_fee,]
        
        simulate.append(temp)
        
    all_simulations = pd.DataFrame(simulate, columns=headers)

    arr_max = all_simulations['arr'].max()
    for i in range(0, all_simulations.shape[0]):
        arr_max = all_simulations['arr'].max()
        multi = arr_max/all_simulations['arr'][i]
        all_simulations.iloc[i, 3] = multi*all_simulations.iloc[i, 3]
        all_simulations.iloc[i, 4] = int(multi*all_simulations.iloc[i, 4])
        all_simulations.iloc[i, 2] = all_simulations.iloc[i, 3]-all_simulations.iloc[i, 4]

    all_simulations['chargers_cost'] = 0
    ch_costs = []
    for i in range(0, all_simulations.shape[0]):
        ch_cost = 0
        for j in all_simulations.iloc[i]['mode']:
            if 'B' in j:
                ch_cost += 5500
            elif 'C' in j:
                ch_cost += 40000
        ch_costs.append(ch_cost)
    all_simulations['chargers_cost'] = ch_costs

    all_simulations['chargers_upgrade'] = 0
    ch_ups = []
    for i in range(0, all_simulations.shape[0]):
        ch_up = 0
        for j in list(set(all_simulations.iloc[i]['mode'])):
            if 'B' in j:
                ch_up += 400
            elif 'C' in j:
                ch_up += 12000
                
        for j in all_simulations.iloc[i]['mode']:
            if 'B' in j:
                ch_up += 100*12
            elif 'C' in j:
                ch_up += 200*12
            
        ch_ups.append(ch_up)
                
    all_simulations['chargers_upgrade'] = ch_ups

    all_simulations['parking_slots'] = 0
    parking_slots = []
    for i in range(0, all_simulations.shape[0]):
        p_s = all_simulations.iloc[i]['qsize']*len(all_simulations.iloc[i]['mode'])*300*12
        parking_slots.append(p_s)
        
    all_simulations['parking_slots'] = parking_slots

    all_simulations['total_cost'] = all_simulations['chargers_cost']+all_simulations['chargers_upgrade']+all_simulations['parking_slots']
    all_simulations['total_profit'] = all_simulations['profit']+all_simulations['park_fee']
    all_simulations['net_profit'] = all_simulations['profit']+all_simulations['park_fee']-(all_simulations['chargers_cost']+all_simulations['chargers_upgrade']+all_simulations['parking_slots'])
    all_simulations['loss_percent'] = (all_simulations['arr']-all_simulations['dep'])/all_simulations['arr']
    all_simulations['ROI'] = (all_simulations['total_profit']-all_simulations['total_cost'])/all_simulations['total_cost']
    all_simulations['sys_delay'] = all_simulations['delay']/all_simulations['dep']
    all_simulations['q_delay'] = (all_simulations['delay']-all_simulations['st'])/all_simulations['dep']

    print("Finished Data Preparation")

    return all_simulations