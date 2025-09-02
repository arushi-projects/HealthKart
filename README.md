# HealthKart Influencer Campaign Dashboard 

## 📌 Project Overview  
This project demonstrates how influencer campaign data can be simulated, engineered, and visualised to provide actionable marketing insights. 

The campaign was designed around **HealthKart**, India’s leading online health and fitness retailer, which houses popular brands like **MuscleBlaze, HK Vitals, TrueBasics, and Nouriza**. Since real campaign data was unavailable, I **simulated 4 core datasets** using analytical guesstimates:  

Since real campaign data was unavailable, I **simulated 4 core datasets** using analytical guesstimates:  
- **Influencers**: profiles with IDs, categories, gender, follower counts, and platforms.  
- **Posts**: influencer activity including reach, likes, and comments.  
- **Tracking Data**: campaign-level outcomes such as orders and revenue.  
- **Payouts**: influencer compensation on a post/order basis.  

The data was designed to **mirror realistic campaign patterns** so the dashboard can be tested as if it were running on live business data.  

---

## 🔧 Approach  

### 1. **Data Simulation**  
- Created 4 datasets (`influencers`, `posts`, `tracking_data`, `payouts`) with randomised but realistic distributions.  
- Used **analytical guesstimates** (e.g., follower tiers, category-platform splits, engagement ratios) to mimic industry trends.  

### 2. **Feature Engineering & KPIs**  
After simulation, I computed **aggregated metrics and KPIs** at influencer and platform levels:  
- **Engagement Metrics** → reach, likes, comments, engagement rate.  
- **Business Metrics** → orders, revenue, ROAS, cost per order, cost per engagement.  
- **Composite Scores** → efficiency score, ROI score.  
- **Derived Features** → follower tiers (Nano/Micro/Macro/Mega), performance categories (High/Medium/Low), persona combinations.  
- **Time-based Metrics** → post frequency, days since last post, campaign duration.  

These were consolidated into a **master dataset**, along with aggregated **platform and persona performance tables**.  

### 3. **Dashboard Development**  
- Built a **Streamlit dashboard** to make the data interactive.  
- Dashboard sections include:  
  - **Executive KPIs** (total revenue, overall ROAS, best/worst performers).  
  - **Influencer Drilldowns** with KPIs, status indicators, and rankings.  
  - **Platform Insights** with comparative performance.  
  - **Persona & Category Analysis** to identify best combinations.  
  - **Investment Actions** (Invest More, Optimise, Monitor groups).  

### 4. **Deployment**  
- Deployed the app on **Streamlit Cloud** for easy sharing and access.  
- Requirements managed via `requirements.txt`.  
- Data (CSVs) included directly in the repo for reproducibility.  

---

## 🚀 How to Run Locally  

1. Clone the repo:  
   ```bash
   git clone https://github.com/your-username/cyclomart-dashboard.git
   cd cyclomart-dashboard
2. Install dependencies:
   pip install -r requirements.txt
3. Run the dashboard:
   streamlit run app.py
4. Run the URL for the Live Dashboard:
   Deployed here [View HealthKart Dashboard](https://healthkart-kfa5wky38wa4nves5zszxf.streamlit.app/)
   
   

