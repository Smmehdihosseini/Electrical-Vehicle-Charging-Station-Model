class Settings(object):
    def __init__(self):
        # Simulation Country
        self.sim_region = 'Italy'
        # Simulation Days
        self.sim_time = 365
        # Minimum Traffic Load
        self.min_traff_load = 0.5
        # Random First Peak Range
        self.first_peak_range = (9, 12)
        # Random Second Peak Range
        self.second_peak_range = (14, 18)
        # Parking Slots
        self.parking_slots = [1, 2, 3]
        # Charger Modes for Each (Level B, Level C)
        self.charger_modes = [(1,0), (0,1), (1,1), (1,2), (2,1),
                                (2,0), (0,2), (3,0), (0,3)]
        # Chargers Cost for Each (Level B, Level C) (EUR)
        self.charger_cost = (5500, 40000)
        # Chargers Facility Upgrades Cost for Each (Level B, Level C) (EUR)
        self.upgrade_cost = (400, 12000)
        # Chargers Maintenance Cost (/Month)
        self.maintenance_cost = (100, 200)
        # Parking Slot Rent Cost (/Month)
        self.parking_slot_cost = 300
        # Parking Fee (EUR/H)
        self.parking_fee = 2.5
        # Save DataFrame as csv file
        self.save_df = True
        # Save DataFrame as csv file
        self.print_df = True

    def run(self):
        pass