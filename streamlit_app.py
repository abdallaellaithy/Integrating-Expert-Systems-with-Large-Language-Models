import streamlit as st
import pandas as pd
import sqlite3
from expert_system import MobileExpertSystem
from local_llm_client import RemoteLLMRecommender
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(
    page_title="Mobile Phone Recommendation DSS",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .recommendation-card {
        background-color: #ffffff;
        color: #000000;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 6px solid #2E86AB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .expert-recommendation {
        border-left-color: #28a745;
        background-color: #f8fff9;
    }
    .llm-recommendation {
        border-left-color: #007bff;
        background-color: #f8fbff;
    }
    .fallback-recommendation {
        border-left-color: #ffc107;
        background-color: #fffdf8;
    }
    .recommendation-card h4 {
        color: #1f1f1f !important;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .score-badge {
        background-color: #2E86AB;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 1rem;
    }
    .status-indicator {
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .status-connected {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-disconnected {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .recommendation-card .stMarkdown p {
        color: #2c2c2c !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        font-family: 'Arial', sans-serif !important;
    }
    .streamlit-expanderContent {
        background-color: #fafafa;
        border-radius: 8px;
        padding: 1rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

class MobileRecommendationApp:
    def __init__(self):
        self.expert_system = MobileExpertSystem()
        self.llm_client = None
        self.db_path = 'mobile_recommendations.db'
        
    def initialize_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mobile_data")
            count = cursor.fetchone()[0]
            conn.close()
            if count == 0:
                st.warning("Database is empty. Please run the database setup script first.")
                return False
            return True
        except:
            st.error("Database not found. Please run the database setup script first.")
            return False
    
    def setup_llm_connection(self):
        st.sidebar.markdown("### LLM Service Configuration")
        
        colab_url = st.sidebar.text_input(
            "Colab ngrok URL",
            placeholder="https://your-ngrok-url.ngrok.io",
            help="Enter the ngrok URL from your Google Colab instance"
        )
        
        if colab_url:
            if 'llm_client' not in st.session_state or st.session_state.get('colab_url') != colab_url:
                try:
                    with st.spinner("Connecting to Colab LLM service..."):
                        self.llm_client = RemoteLLMRecommender(colab_url)
                        st.session_state.llm_client = self.llm_client
                        st.session_state.colab_url = colab_url
                        st.session_state.llm_connected = True
                except Exception as e:
                    st.session_state.llm_connected = False
                    st.session_state.llm_error = str(e)
            else:
                self.llm_client = st.session_state.llm_client
        
        if colab_url:
            if st.session_state.get('llm_connected', False):
                st.sidebar.markdown(
                    '<span class="status-indicator status-connected">LLM Connected</span>',
                    unsafe_allow_html=True
                )
            else:
                st.sidebar.markdown(
                    '<span class="status-indicator status-disconnected">LLM Disconnected</span>',
                    unsafe_allow_html=True
                )
                if 'llm_error' in st.session_state:
                    st.sidebar.error(f"Error: {st.session_state.llm_error}")
        else:
            st.sidebar.info("Enter Colab URL to enable LLM recommendations")
    
    def get_user_preferences(self):
        st.sidebar.markdown("## Your Preferences")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            price_range = st.selectbox(
                "Price Range",
                ["Low", "Low-Medium", "Medium", "Medium-High", "High"],
                index=2
            )
            
            ram = st.selectbox(
                "RAM (GB)",
                [4, 6, 8, 12, 16],
                index=2
            )
            
            storage = st.selectbox(
                "Storage (GB)",
                [64, 128, 256, 512],
                index=1
            )
            
            camera_mp = st.selectbox(
                "Camera (MP)",
                [12, 48, 50, 64, 108, 200],
                index=2
            )
            
            battery_mah = st.selectbox(
                "Battery (mAh)",
                [3000, 4000, 4500, 5000, 5400],
                index=2
            )
        
        with col2:
            screen_size = st.slider(
                "Screen Size (inches)",
                min_value=5.0,
                max_value=7.0,
                value=6.2,
                step=0.1
            )
            
            operating_system = st.selectbox(
                "Operating System",
                ["iOS", "Android"],
                index=1
            )
            
            processor_type = st.selectbox(
                "Processor Preference",
                ["A17 Pro", "A16 Bionic", "A15 Bionic", "Snapdragon 8 Gen 3", 
                 "Snapdragon 8 Gen 2", "Google Tensor G3", "MediaTek Dimensity 9000",
                 "Exynos 1380", "MediaTek Helio G85"],
                index=3
            )
            
            network_type = st.selectbox(
                "Network",
                ["4G", "5G"],
                index=1
            )
        
        return {
            'price_range': price_range,
            'ram': ram,
            'storage': storage,
            'camera_mp': camera_mp,
            'battery_mah': battery_mah,
            'screen_size': screen_size,
            'operating_system': operating_system,
            'processor_type': processor_type,
            'network_type': network_type
        }
    
    def display_expert_recommendations(self, recommendations):
        st.markdown("### Expert System Recommendations")
        
        for i, rec in enumerate(recommendations, 1):
            with st.container():
                st.markdown(f"""
                <div class="recommendation-card expert-recommendation">
                    <h4>#{i} {rec['brand']} {rec['model']} 
                        <span class="score-badge">Score: {rec['final_score']:.3f}</span>
                    </h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Price Range:** {rec['price_range']}")
                    st.write(f"**RAM:** {rec['ram']}GB")
                    st.write(f"**Storage:** {rec['storage']}GB")
                
                with col2:
                    st.write(f"**Camera:** {rec['camera_mp']}MP")
                    st.write(f"**Battery:** {rec['battery_mah']}mAh")
                    st.write(f"**Screen:** {rec['screen_size']}\"")
                
                with col3:
                    st.write(f"**OS:** {rec['operating_system']}")
                    st.write(f"**Processor:** {rec['processor_type']}")
                    st.write(f"**Network:** {rec['network_type']}")
                
                with st.expander(f"Score Breakdown for {rec['brand']} {rec['model']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Similarity Score", f"{rec['similarity_score']:.3f}")
                    with col2:
                        st.metric("Rule Bonus", f"{rec['rule_bonus']:.3f}")
                    with col3:
                        st.metric("Historical Bonus", f"{rec['historical_bonus']:.3f}")
                
                st.markdown("---")
    
    def display_llm_recommendations(self, recommendations):
        st.markdown("### AI Language Model Recommendations")
        
        if not recommendations:
            if st.session_state.get('llm_connected', False):
                st.info("No LLM recommendations available. The service may be processing or encountering issues.")
            else:
                st.info("Enable LLM Recommendations: Enter your Colab ngrok URL in the sidebar to get AI-powered recommendations!")
            return
        
        for i, rec in enumerate(recommendations, 1):
            card_class = "llm-recommendation"
            source_icon = ""
            if rec.get('source') == 'Fallback':
                card_class = "fallback-recommendation"
                source_icon = ""
            
            with st.container():
                st.markdown(f"""
                <div class="recommendation-card {card_class}">
                    <h4>{source_icon} #{i} {rec['brand']} {rec['model']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Price Range:** {rec['price_range']}")
                    st.write(f"**RAM:** {rec['ram']}GB | **Storage:** {rec['storage']}GB")
                    st.write(f"**Camera:** {rec['camera_mp']}MP | **Battery:** {rec['battery_mah']}mAh")
                    st.write(f"**OS:** {rec['operating_system']} | **Network:** {rec['network_type']}")
                
                with col2:
                    st.write(f"**Screen:** {rec['screen_size']}\"")
                    st.write(f"**Processor:** {rec['processor_type']}")
                    if rec.get('source'):
                        st.write(f"**Source:** {rec['source']}")
                
                if 'llm_reasoning' in rec:
                    with st.expander(f"AI Reasoning for {rec['brand']} {rec['model']}"):
                        st.write(rec['llm_reasoning'])
                
                st.markdown("---")
    
    def display_analytics(self):
        st.markdown("### System Analytics")
        
        conn = sqlite3.connect(self.db_path)
        
        user_choices = pd.read_sql_query("SELECT * FROM user_choices", conn)
        mobile_data = pd.read_sql_query("SELECT * FROM mobile_data", conn)
        
        if not user_choices.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                brand_counts = user_choices['chosen_brand'].value_counts()
                fig_brands = px.pie(
                    values=brand_counts.values,
                    names=brand_counts.index,
                    title="Most Popular Brands (User Choices)"
                )
                st.plotly_chart(fig_brands, use_container_width=True)
            
            with col2:
                source_counts = user_choices['recommendation_source'].value_counts()
                fig_sources = px.bar(
                    x=source_counts.index,
                    y=source_counts.values,
                    title="Recommendation Sources"
                )
                st.plotly_chart(fig_sources, use_container_width=True)
            
            price_counts = user_choices['price_range'].value_counts()
            fig_price = px.bar(
                x=price_counts.index,
                y=price_counts.values,
                title="Price Range Preferences",
                color=price_counts.values,
                color_continuous_scale="viridis"
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.markdown("#### Available Mobile Database")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Mobiles", len(mobile_data))
        with col2:
            st.metric("Unique Brands", mobile_data['brand'].nunique())
        with col3:
            st.metric("Average RAM", f"{mobile_data['ram'].mean():.1f}GB")
        with col4:
            st.metric("User Choices", len(user_choices))
        
        conn.close()
    
    def save_final_choice(self, user_preferences, chosen_mobile, source):
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
            source
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
    
    def run(self):
        st.markdown('<h1 class="main-header">Mobile Phone Recommendation System</h1>', unsafe_allow_html=True)
        
        if not self.initialize_database():
            st.stop()
        
        self.setup_llm_connection()
        
        tab1 = st.tabs(["Get Recommendations"])[0]
        
        with tab1:
            user_preferences = self.get_user_preferences()
            
            if st.sidebar.button("Get Recommendations", type="primary"):
                with st.spinner("Generating recommendations..."):
                    expert_recommendations = self.expert_system.get_expert_recommendations(user_preferences, 8)
                    
                    llm_recommendations = []
                    if st.session_state.get('llm_connected', False) and self.llm_client:
                        try:
                            llm_recommendations = self.llm_client.get_llm_recommendations(user_preferences, 2)
                        except Exception as e:
                            st.error(f"LLM service error: {e}")
                            llm_recommendations = []
                    
                    st.session_state.expert_recs = expert_recommendations
                    st.session_state.llm_recs = llm_recommendations
                    st.session_state.user_prefs = user_preferences
            
            if 'expert_recs' in st.session_state:
                self.display_expert_recommendations(st.session_state.expert_recs)
                
                self.display_llm_recommendations(st.session_state.llm_recs)
                
                st.markdown("### Make Your Final Choice")
                
                all_recs = st.session_state.expert_recs + st.session_state.llm_recs
                choice_options = [f"{rec['brand']} {rec['model']}" for rec in all_recs]
                
                if choice_options:
                    selected_choice = st.selectbox("Choose your preferred mobile:", ["None"] + choice_options)
                    
                    if selected_choice != "None" and st.button("Confirm Choice"):
                        selected_mobile = None
                        source = ""
                        
                        for rec in st.session_state.expert_recs:
                            if f"{rec['brand']} {rec['model']}" == selected_choice:
                                selected_mobile = rec
                                source = "Expert System"
                                break
                        
                        if not selected_mobile:
                            for rec in st.session_state.llm_recs:
                                if f"{rec['brand']} {rec['model']}" == selected_choice:
                                    selected_mobile = rec
                                    source = rec.get('source', 'LLM')
                                    break
                        
                        if selected_mobile:
                            self.save_final_choice(st.session_state.user_prefs, selected_mobile, source)
                            st.success(f"Thank you! Your choice of {selected_choice} has been saved to improve future recommendations.")
                            st.balloons()

if __name__ == "__main__":
    app = MobileRecommendationApp()
    app.run()