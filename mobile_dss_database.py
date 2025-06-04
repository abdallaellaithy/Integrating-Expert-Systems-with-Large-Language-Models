import sqlite3
import pandas as pd
import random

def create_database():
    conn = sqlite3.connect('mobile_recommendations.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mobile_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        price_range TEXT NOT NULL,
        ram INTEGER NOT NULL,
        storage INTEGER NOT NULL,
        camera_mp INTEGER NOT NULL,
        battery_mah INTEGER NOT NULL,
        screen_size REAL NOT NULL,
        operating_system TEXT NOT NULL,
        processor_type TEXT NOT NULL,
        network_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_choices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        price_range TEXT NOT NULL,
        ram INTEGER NOT NULL,
        storage INTEGER NOT NULL,
        camera_mp INTEGER NOT NULL,
        battery_mah INTEGER NOT NULL,
        screen_size REAL NOT NULL,
        operating_system TEXT NOT NULL,
        processor_type TEXT NOT NULL,
        network_type TEXT NOT NULL,
        chosen_brand TEXT NOT NULL,
        chosen_model TEXT NOT NULL,
        recommendation_source TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    mobile_data = [
        ('Apple', 'iPhone 15 Pro Max', 'High', 8, 256, 48, 4441, 6.7, 'iOS', 'A17 Pro', '5G'),
        ('Apple', 'iPhone 15 Pro', 'High', 8, 128, 48, 3274, 6.1, 'iOS', 'A17 Pro', '5G'),
        ('Apple', 'iPhone 15', 'Medium-High', 6, 128, 48, 3349, 6.1, 'iOS', 'A16 Bionic', '5G'),
        ('Apple', 'iPhone 14', 'Medium', 6, 128, 12, 3279, 6.1, 'iOS', 'A15 Bionic', '5G'),
        ('Apple', 'iPhone SE', 'Low-Medium', 4, 64, 12, 2018, 4.7, 'iOS', 'A15 Bionic', '4G'),
        ('Samsung', 'Galaxy S24 Ultra', 'High', 12, 256, 200, 5000, 6.8, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('Samsung', 'Galaxy S24', 'Medium-High', 8, 128, 50, 4000, 6.2, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('Samsung', 'Galaxy A54', 'Medium', 8, 128, 50, 5000, 6.4, 'Android', 'Exynos 1380', '5G'),
        ('Samsung', 'Galaxy A34', 'Low-Medium', 6, 128, 48, 5000, 6.6, 'Android', 'MediaTek Dimensity 1080', '5G'),
        ('Samsung', 'Galaxy A14', 'Low', 4, 64, 50, 5000, 6.6, 'Android', 'MediaTek Helio G80', '4G'),
        ('Google', 'Pixel 8 Pro', 'High', 12, 128, 50, 5050, 6.7, 'Android', 'Google Tensor G3', '5G'),
        ('Google', 'Pixel 8', 'Medium-High', 8, 128, 50, 4575, 6.2, 'Android', 'Google Tensor G3', '5G'),
        ('Google', 'Pixel 7a', 'Medium', 8, 128, 64, 4385, 6.1, 'Android', 'Google Tensor G2', '5G'),
        ('OnePlus', 'OnePlus 12', 'High', 12, 256, 50, 5400, 6.82, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('OnePlus', 'OnePlus 11', 'Medium-High', 8, 128, 50, 5000, 6.7, 'Android', 'Snapdragon 8 Gen 2', '5G'),
        ('OnePlus', 'OnePlus Nord 3', 'Medium', 8, 128, 50, 5000, 6.74, 'Android', 'MediaTek Dimensity 9000', '5G'),
        ('Xiaomi', 'Xiaomi 14 Ultra', 'High', 16, 512, 50, 5300, 6.73, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('Xiaomi', 'Xiaomi 14', 'Medium-High', 8, 256, 50, 4610, 6.36, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('Xiaomi', 'Redmi Note 13 Pro', 'Medium', 8, 256, 200, 5100, 6.67, 'Android', 'Snapdragon 7s Gen 2', '5G'),
        ('Xiaomi', 'Redmi 13C', 'Low', 4, 128, 50, 5000, 6.74, 'Android', 'MediaTek Helio G85', '4G'),
        ('Huawei', 'P60 Pro', 'High', 8, 256, 48, 4815, 6.67, 'Android', 'Snapdragon 8+ Gen 1', '5G'),
        ('Huawei', 'Nova 11', 'Medium', 8, 256, 50, 4500, 6.7, 'Android', 'Snapdragon 778G', '4G'),
        ('Oppo', 'Find X7 Ultra', 'High', 16, 512, 50, 5000, 6.82, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('Oppo', 'Reno 11', 'Medium', 8, 256, 50, 5000, 6.7, 'Android', 'MediaTek Dimensity 8050', '5G'),
        ('Vivo', 'X100 Pro', 'High', 12, 256, 50, 5400, 6.78, 'Android', 'MediaTek Dimensity 9300', '5G'),
        ('Vivo', 'V29', 'Medium', 8, 256, 50, 4600, 6.78, 'Android', 'Snapdragon 778G', '5G'),
        ('Realme', 'GT 5 Pro', 'Medium-High', 12, 256, 50, 5400, 6.7, 'Android', 'Snapdragon 8 Gen 3', '5G'),
        ('Realme', 'C67', 'Low', 6, 128, 108, 5000, 6.72, 'Android', 'Snapdragon 685', '4G'),
        ('Motorola', 'Edge 50 Ultra', 'High', 12, 512, 50, 4500, 6.7, 'Android', 'Snapdragon 8s Gen 3', '5G'),
        ('Motorola', 'Moto G84', 'Medium', 8, 256, 50, 5000, 6.55, 'Android', 'Snapdragon 695', '5G'),
        ('Nothing', 'Phone (2)', 'Medium-High', 8, 256, 50, 4700, 6.7, 'Android', 'Snapdragon 8+ Gen 1', '5G'),
    ]
    
    cursor.executemany('''
    INSERT INTO mobile_data (brand, model, price_range, ram, storage, camera_mp, battery_mah, screen_size, operating_system, processor_type, network_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', mobile_data)
    
    sample_choices = []
    brands = ['Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi']
    
    for _ in range(50):
        price_range = random.choice(['Low', 'Low-Medium', 'Medium', 'Medium-High', 'High'])
        ram = random.choice([4, 6, 8, 12, 16])
        storage = random.choice([64, 128, 256, 512])
        camera_mp = random.choice([12, 48, 50, 64, 108, 200])
        battery_mah = random.choice([3000, 4000, 5000, 5400])
        screen_size = round(random.uniform(5.5, 6.8), 1)
        os = random.choice(['iOS', 'Android'])
        processor = random.choice(['A17 Pro', 'Snapdragon 8 Gen 3', 'MediaTek Dimensity 9000'])
        network = random.choice(['4G', '5G'])
        chosen_brand = random.choice(brands)
        chosen_model = f"{chosen_brand} Model {random.randint(1, 10)}"
        source = random.choice(['Expert System', 'LLM'])
        
        sample_choices.append((price_range, ram, storage, camera_mp, battery_mah, 
                             screen_size, os, processor, network, chosen_brand, 
                             chosen_model, source))
    
    cursor.executemany('''
    INSERT INTO user_choices (price_range, ram, storage, camera_mp, battery_mah, screen_size, 
                             operating_system, processor_type, network_type, chosen_brand, 
                             chosen_model, recommendation_source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_choices)
    
    conn.commit()
    conn.close()
    print("Database created successfully with sample data!")

def get_mobile_data():
    """Retrieve all mobile data from database"""
    conn = sqlite3.connect('mobile_recommendations.db')
    df = pd.read_sql_query("SELECT * FROM mobile_data", conn)
    conn.close()
    return df

def get_user_choices():
    """Retrieve all user choice data from database"""
    conn = sqlite3.connect('mobile_recommendations.db')
    df = pd.read_sql_query("SELECT * FROM user_choices", conn)
    conn.close()
    return df

def add_user_choice(choice_data):
    """Add new user choice to database"""
    conn = sqlite3.connect('mobile_recommendations.db')
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
    create_database()
    print("Mobile data sample:")
    print(get_mobile_data().head())
    print("\nUser choices sample:")
    print(get_user_choices().head())