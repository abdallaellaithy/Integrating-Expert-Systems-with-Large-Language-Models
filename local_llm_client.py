import requests
import sqlite3
import pandas as pd
import json
import time

class RemoteLLMRecommender:
    def __init__(self, colab_url, db_path='mobile_recommendations.db'):
        self.colab_url = colab_url.rstrip('/')
        self.db_path = db_path
        self.timeout = 60
        self.test_connection()
    
    def test_connection(self):
        try:
            response = requests.get(f"{self.colab_url}/health", timeout=10)
            if response.status_code == 200:
                print("Successfully connected to Colab LLM service")
                return True
            else:
                print("Colab LLM service is not responding correctly")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to Colab LLM service: {e}")
            print("Make sure:")
            print("1. Your Colab notebook is running")
            print("2. The ngrok URL is correct")
            print("3. The ngrok tunnel is active")
            return False
    
    def load_mobile_data(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM mobile_data", conn)
        conn.close()
        return df
    
    def format_mobile_database_for_llm(self, mobile_data):
        mobile_db_text = ""
        for i, mobile in mobile_data.iterrows():
            mobile_db_text += f"{i+1}. {mobile['brand']} {mobile['model']} - "
            mobile_db_text += f"Price: {mobile['price_range']}, "
            mobile_db_text += f"RAM: {mobile['ram']}GB, "
            mobile_db_text += f"Storage: {mobile['storage']}GB, "
            mobile_db_text += f"Camera: {mobile['camera_mp']}MP, "
            mobile_db_text += f"Battery: {mobile['battery_mah']}mAh, "
            mobile_db_text += f"Screen: {mobile['screen_size']}\", "
            mobile_db_text += f"OS: {mobile['operating_system']}, "
            mobile_db_text += f"Processor: {mobile['processor_type']}, "
            mobile_db_text += f"Network: {mobile['network_type']}\n"
        return mobile_db_text
    
    def get_llm_recommendations(self, user_preferences, num_recommendations=2):
        mobile_data = self.load_mobile_data()
        mobile_db_text = self.format_mobile_database_for_llm(mobile_data)
        request_data = {
            'user_preferences': user_preferences,
            'mobile_database': mobile_db_text,
            'num_recommendations': num_recommendations
        }
        try:
            print("Requesting recommendations from Colab LLM...")
            response = requests.post(
                f"{self.colab_url}/recommend",
                json=request_data,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    matched_recommendations = self.match_recommendations_to_database(
                        result['recommendations'], 
                        result['reasoning'],
                        mobile_data
                    )
                    print(f"Received {len(matched_recommendations)} LLM recommendations")
                    return matched_recommendations
                else:
                    print(f"LLM service returned error: {result.get('error', 'Unknown error')}")
                    return self.get_fallback_recommendations(user_preferences, mobile_data, num_recommendations)
            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return self.get_fallback_recommendations(user_preferences, mobile_data, num_recommendations)
        except requests.exceptions.Timeout:
            print("Request timed out. LLM processing is taking too long.")
            return self.get_fallback_recommendations(user_preferences, mobile_data, num_recommendations)
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return self.get_fallback_recommendations(user_preferences, mobile_data, num_recommendations)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self.get_fallback_recommendations(user_preferences, mobile_data, num_recommendations)
    
    def match_recommendations_to_database(self, recommendations, reasoning, mobile_data):
        matched_recommendations = []
        for rec_text in recommendations:
            matched_mobile = self.find_mobile_in_database(rec_text, mobile_data)
            if matched_mobile is not None:
                mobile_info = mobile_data.iloc[matched_mobile].to_dict()
                mobile_info['llm_reasoning'] = reasoning
                mobile_info['recommendation_text'] = rec_text
                mobile_info['source'] = 'LLM'
                matched_recommendations.append(mobile_info)
            else:
                print(f"Could not match recommendation: {rec_text}")
        return matched_recommendations
    
    def find_mobile_in_database(self, recommendation_text, mobile_data):
        recommendation_lower = recommendation_text.lower()
        best_match_idx = None
        best_match_score = 0
        for idx, mobile in mobile_data.iterrows():
            mobile_text = f"{mobile['brand']} {mobile['model']}".lower()
            brand_match = mobile['brand'].lower() in recommendation_lower
            model_words = mobile['model'].lower().split()
            model_match = any(word in recommendation_lower for word in model_words if len(word) > 2)
            if mobile_text in recommendation_lower:
                return idx
            match_score = 0
            if brand_match:
                match_score += 2
            if model_match:
                match_score += 3
            if match_score > best_match_score:
                best_match_score = match_score
                best_match_idx = idx
        return best_match_idx if best_match_score > 0 else None
    
    def get_fallback_recommendations(self, user_preferences, mobile_data, num_recommendations):
        print("Using fallback recommendations...")
        filtered_mobiles = mobile_data[
            (mobile_data['price_range'] == user_preferences['price_range']) |
            (mobile_data['operating_system'] == user_preferences['operating_system'])
        ]
        if filtered_mobiles.empty:
            filtered_mobiles = mobile_data
        recommendations = []
        for _, mobile in filtered_mobiles.head(num_recommendations).iterrows():
            mobile_dict = mobile.to_dict()
            mobile_dict['llm_reasoning'] = "Fallback recommendation due to LLM service unavailability. Based on basic preference matching."
            mobile_dict['recommendation_text'] = f"{mobile['brand']} {mobile['model']}"
            mobile_dict['source'] = 'Fallback'
            recommendations.append(mobile_dict)
        return recommendations
    
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
            'LLM'
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
    print("Testing LLM Client")
    print("=" * 50)
    test_url = input("Enter your Colab ngrok URL for testing (or press Enter to skip): ").strip()
    if not test_url:
        print("Skipping test. Use the web app to test with your Colab URL.")
        exit()
    try:
        print(f"Connecting to: {test_url}")
        llm_client = RemoteLLMRecommender(test_url)
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
        print("Testing with sample preferences...")
        print("Getting recommendations (this may take 30-60 seconds)...")
        recommendations = llm_client.get_llm_recommendations(user_prefs)
        print(f"\nReceived {len(recommendations)} recommendations:")
        print("=" * 50)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['brand']} {rec['model']}")
            print(f"   Source: {rec.get('source', 'Unknown')}")
            if 'llm_reasoning' in rec:
                print(f"   Reasoning: {rec['llm_reasoning'][:100]}...")
            print()
        print("Test completed successfully")