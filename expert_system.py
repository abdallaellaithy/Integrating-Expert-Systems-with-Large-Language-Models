import sqlite3
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder, StandardScaler
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

class MobileExpertSystem:
    def __init__(self, db_path='mobile_recommendations.db'):
        self.db_path = db_path
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_weights = {
            'price_range': 0.25,
            'ram': 0.20,
            'storage': 0.15,
            'camera_mp': 0.15,
            'battery_mah': 0.10,
            'screen_size': 0.05,
            'operating_system': 0.05,
            'processor_type': 0.03,
            'network_type': 0.02
        }
        
    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        self.mobile_data = pd.read_sql_query("SELECT * FROM mobile_data", conn)
        self.user_choices = pd.read_sql_query("SELECT * FROM user_choices", conn)
        conn.close()
        
    def preprocess_data(self):
        all_data = pd.concat([
            self.mobile_data[['price_range', 'ram', 'storage', 'camera_mp', 'battery_mah', 
                             'screen_size', 'operating_system', 'processor_type', 'network_type']],
            self.user_choices[['price_range', 'ram', 'storage', 'camera_mp', 'battery_mah', 
                              'screen_size', 'operating_system', 'processor_type', 'network_type']]
        ], ignore_index=True)
        
        categorical_cols = ['price_range', 'operating_system', 'processor_type', 'network_type']
        
        for col in categorical_cols:
            le = LabelEncoder()
            all_data[col + '_encoded'] = le.fit_transform(all_data[col].astype(str))
            self.label_encoders[col] = le
        
        feature_cols = ['price_range_encoded', 'ram', 'storage', 'camera_mp', 'battery_mah', 
                       'screen_size', 'operating_system_encoded', 'processor_type_encoded', 
                       'network_type_encoded']
        
        self.scaler.fit(all_data[feature_cols])
        
    def calculate_similarity_score(self, user_preferences, mobile_specs):
        user_encoded = []
        mobile_encoded = []
        
        features = ['price_range', 'ram', 'storage', 'camera_mp', 'battery_mah', 
                   'screen_size', 'operating_system', 'processor_type', 'network_type']
        
        for feature in features:
            if feature in ['price_range', 'operating_system', 'processor_type', 'network_type']:
                try:
                    user_val = self.label_encoders[feature].transform([str(user_preferences[feature])])[0]
                    mobile_val = self.label_encoders[feature].transform([str(mobile_specs[feature])])[0]
                except:
                    user_val = 0
                    mobile_val = 0
            else:
                user_val = float(user_preferences[feature])
                mobile_val = float(mobile_specs[feature])
            
            user_encoded.append(user_val)
            mobile_encoded.append(mobile_val)
        
        user_array = np.array(user_encoded).reshape(1, -1)
        mobile_array = np.array(mobile_encoded).reshape(1, -1)
        
        user_normalized = self.scaler.transform(user_array)
        mobile_normalized = self.scaler.transform(mobile_array)
        
        similarity = cosine_similarity(user_normalized, mobile_normalized)[0][0]
        
        return similarity
    
    def get_expert_recommendations(self, user_preferences, num_recommendations=8):
        self.load_data()
        self.preprocess_data()
        
        recommendations = []
        
        for _, mobile in self.mobile_data.iterrows():
            mobile_specs = {
                'price_range': mobile['price_range'],
                'ram': mobile['ram'],
                'storage': mobile['storage'],
                'camera_mp': mobile['camera_mp'],
                'battery_mah': mobile['battery_mah'],
                'screen_size': mobile['screen_size'],
                'operating_system': mobile['operating_system'],
                'processor_type': mobile['processor_type'],
                'network_type': mobile['network_type']
            }
            
            similarity_score = self.calculate_similarity_score(user_preferences, mobile_specs)
            rule_bonus = self.apply_expert_rules(user_preferences, mobile_specs)
            historical_bonus = self.calculate_historical_preference_bonus(user_preferences, mobile['brand'])
            final_score = similarity_score + rule_bonus + historical_bonus
            
            recommendations.append({
                'brand': mobile['brand'],
                'model': mobile['model'],
                'price_range': mobile['price_range'],
                'ram': mobile['ram'],
                'storage': mobile['storage'],
                'camera_mp': mobile['camera_mp'],
                'battery_mah': mobile['battery_mah'],
                'screen_size': mobile['screen_size'],
                'operating_system': mobile['operating_system'],
                'processor_type': mobile['processor_type'],
                'network_type': mobile['network_type'],
                'similarity_score': similarity_score,
                'rule_bonus': rule_bonus,
                'historical_bonus': historical_bonus,
                'final_score': final_score
            })
        
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def apply_expert_rules(self, user_prefs, mobile_specs):
        bonus = 0.0
        
        if user_prefs['price_range'] == mobile_specs['price_range']:
            bonus += 0.2
        if mobile_specs['ram'] >= user_prefs['ram']:
            bonus += 0.1
        elif mobile_specs['ram'] < user_prefs['ram']:
            bonus -= 0.15
        if mobile_specs['storage'] >= user_prefs['storage']:
            bonus += 0.1
        elif mobile_specs['storage'] < user_prefs['storage']:
            bonus -= 0.1
        if user_prefs['operating_system'] == mobile_specs['operating_system']:
            bonus += 0.15
        if user_prefs['camera_mp'] >= 48 and mobile_specs['camera_mp'] >= 48:
            bonus += 0.1
        if user_prefs['battery_mah'] >= 4500 and mobile_specs['battery_mah'] >= 4500:
            bonus += 0.08
        if user_prefs['network_type'] == '5G' and mobile_specs['network_type'] == '5G':
            bonus += 0.05
        size_diff = abs(mobile_specs['screen_size'] - user_prefs['screen_size'])
        if size_diff <= 0.3:
            bonus += 0.05
        elif size_diff > 1.0:
            bonus -= 0.05
        
        return bonus
    
    def calculate_historical_preference_bonus(self, user_prefs, brand):
        if self.user_choices.empty:
            return 0.0
        
        similar_users = self.user_choices[
            (self.user_choices['price_range'] == user_prefs['price_range']) |
            (self.user_choices['operating_system'] == user_prefs['operating_system'])
        ]
        
        if similar_users.empty:
            return 0.0
        
        brand_counts = Counter(similar_users['chosen_brand'])
        total_similar_choices = len(similar_users)
        
        if brand in brand_counts:
            brand_preference_ratio = brand_counts[brand] / total_similar_choices
            return brand_preference_ratio * 0.1
        
        return 0.0
    
    def save_user_choice(self, user_preferences, chosen_mobile):
        choice_data = (
            user_preferences['price_range'],
            user_preferences['ram'],
            user_preferences['storage'],
            user_preferences['camera_mp'],
            user_preferences['battery_mah'],
            user_preferences['screen_size'],
            user_preferences['operating_system'],
            user_preferences['processor_type'],
            user_preferences['network_type'],
            chosen_mobile['brand'],
            chosen_mobile['model'],
            'Expert System'
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO user_choices (price_range, ram, storage, camera_mp, battery_mah, screen_size, 
                                 operating_system, processor_type, network_type, chosen_brand, 
                                 chosen_model, recommendation_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', choice_data)
        
        conn.commit()
        conn.close()

if __name__ == "__main__":
    expert_system = MobileExpertSystem()
    
    user_prefs = {
        'price_range': 'Medium',
        'ram': 8,
        'storage': 128,
        'camera_mp': 50,
        'battery_mah': 4500,
        'screen_size': 6.2,
        'operating_system': 'Android',
        'processor_type': 'Snapdragon 8 Gen 3',
        'network_type': '5G'
    }
    
    recommendations = expert_system.get_expert_recommendations(user_prefs)
    
    print("Expert System Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['brand']} {rec['model']} - Score: {rec['final_score']:.2f}")