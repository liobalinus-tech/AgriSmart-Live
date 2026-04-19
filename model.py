import numpy as np

class HarvestEngine:
    def __init__(self):
        self.PH_BOUNDS = (4.0, 9.0)
        self.RAIN_BOUNDS = (300.0, 2000.0)
        self.weights = np.array([1.5, 1.0])
        
        # Raw Ideals (for comparison logic)
        self.ideals = {
            "Maize (White/Yellow)": {"ph": 6.5, "rain": 800},
            "Highland Rice": {"ph": 5.5, "rain": 1500},
            "Drought-Resistant Sorghum": {"ph": 7.5, "rain": 500},
            "Cassava (Root Crop)": {"ph": 5.0, "rain": 1100}
        }
        
        # Normalized Centroids for the Math
        self.crop_ideals = {k: self._norm(v['ph'], v['rain']) for k, v in self.ideals.items()}

    def _norm(self, ph, rain):
        p = (ph - self.PH_BOUNDS[0]) / (self.PH_BOUNDS[1] - self.PH_BOUNDS[0])
        r = (rain - self.RAIN_BOUNDS[0]) / (self.RAIN_BOUNDS[1] - self.RAIN_BOUNDS[0])
        return np.array([p, r])

    def analyze_constraints(self, user_ph, user_rain):
        analysis = {}
        for crop, ideal in self.ideals.items():
            reasons = []
            # pH Logic
            if user_ph > ideal['ph'] + 0.8: reasons.append("Soil is too alkaline for this crop.")
            elif user_ph < ideal['ph'] - 0.8: reasons.append("Soil is too acidic for this crop.")
            
            # Rain Logic
            if user_rain > ideal['rain'] + 300: reasons.append("Rainfall is too high; risk of root rot/fungus.")
            elif user_rain < ideal['rain'] - 300: reasons.append("Rainfall is too low; crop may suffer drought stress.")
            
            analysis[crop] = reasons if reasons else ["Environmental conditions are favorable."]
        return analysis

    def calculate_yield_potential(self, ph, rain):
        user_vec = self._norm(ph, rain)
        suitability = {crop: np.exp(-np.linalg.norm((user_vec - ideal) * self.weights)) 
                       for crop, ideal in self.crop_ideals.items()}
        top_crop = max(suitability, key=suitability.get)
        return top_crop, suitability[top_crop], suitability