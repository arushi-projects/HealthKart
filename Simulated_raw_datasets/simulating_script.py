import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)


# some categorical input values
categories = ["health", "nutrition", "medical", "bodybuilding", "sports"]
platforms = ['YouTube', 'Instagram', 'X', 'Facebook']
platform_weights = [0.30, 0.45, 0.20, 0.05] #based on guestimates
genders = ['Male', 'Female']
gender_weights = [0.65, 0.35] #based on assumption that fitness and bodybuilder influencers are more males than females in india
products = {"Protein Powder": 1200, "Omega 3": 850, "Multivitamins": 500, "Energy Drink": 100, "Knee Support": 2400} #randomly chosen
num_influencers = 25 #numbers taken for now
num_posts = 40
num_users = 1000

# Helper functions
def generate_name():
    first_names = ['Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayaan', 'Krishna', 'Ishaan',
                   'Ananya', 'Diya', 'Isha', 'Jhanvi', 'Myra', 'Saanvi', 'Sara', 'Tanya', 'Zara', 'Kiara']
    last_names = ['Sharma', 'Verma', 'Mishra', 'Reddy', 'Patel', 'Gupta', 'Mehta', 'Kapoor', 'Joshi', 'Desai']
    return f"{random.choice(first_names)} {random.choice(last_names)}" #this function will be used to generate random names

def generate_url(post_id): return f"https://socialmedia.com/post/{post_id}" #this function will be used to generate random URLs


#Influencers dataset
influencers = []
for i in range(num_influencers):
    influencer_id = f"INF{str(i+1).zfill(3)}"
    name = generate_name()
    gender = np.random.choice(genders, p=gender_weights)
    category = random.choice(categories)
    platform = np.random.choice(platforms, p=platform_weights)
    followers = int(np.clip(np.random.normal(850_000, 1_800_000), 10_000, 10_000_000))
    influencers.append([influencer_id, name, category, gender, followers, platform])

influencers_df = pd.DataFrame(influencers, columns=["influencer_id", "name", "category", "gender", "follower_count", "platform"])

# 2. Posts dataset
posts = []
for i in range(num_posts):
    post_id = f"POST{str(i+1).zfill(3)}"
    influencer = influencers_df.sample(1).iloc[0] #selects influencers from the database randomly
    influencer_id = influencer["influencer_id"]
    platform = influencer["platform"]
    post_date = datetime.today() - timedelta(days=random.randint(1, 90)) #generates random dates
    url = generate_url(i+1)
    caption = f"Check out this amazing product! #{random.choice(categories)}"
    reach = int(influencer["follower_count"] * np.random.uniform(0.1, 0.6))
    likes = int(reach * np.random.uniform(0.05, 0.15))
    comments = int(reach * np.random.uniform(0.005, 0.02))
    posts.append([post_id, influencer_id, platform, post_date.strftime('%Y-%m-%d'), url, caption, reach, likes, comments])

posts_df = pd.DataFrame(posts, columns=["post_id","influencer_id", "platform", "date", "URL", "caption", "reach", "likes", "comments"])

# 3. Tracking data
tracking = []
for i in range(num_posts * 10):
    post = posts_df.sample(1).iloc[0]
    post_id = post["post_id"]
    influencer_id = post["influencer_id"]
    source = post["platform"]
    campaign = f"Campaign_{random.randint(1,5)}" #assuming that each campaign has a serial associated with it
    user_id = f"USER{random.randint(1, num_users)}" #randomly assinging user id
    product = random.choice(list(products.keys())) #randomly selects the products from the products list (assuming that a post can lead to orders for any of the products)
    date = post["date"]
    orders = np.random.poisson(2)
    revenue = round(orders * products[product] * np.random.uniform(0.9, 1.1), 2)
    tracking.append([source, campaign, post_id, influencer_id, user_id, product, date, orders, revenue])

tracking_df = pd.DataFrame(tracking, columns=["source", "campaign", "post_id", "influencer_id", "user_id", "product", "date", "orders", "revenue"])

# 4. Payouts
payouts = []
for influencer_id in influencers_df["influencer_id"]:
    basis = np.random.choice(["post", "order"])
    rate = round(np.random.uniform(500, 5000), 2) if basis == "post" else round(np.random.uniform(50, 500), 2)
    influencer_posts = posts_df[posts_df["influencer_id"] == influencer_id]
    influencer_orders = tracking_df[tracking_df["influencer_id"] == influencer_id]["orders"].sum()
    total_payout = len(influencer_posts) * rate if basis == "post" else influencer_orders * rate
    payouts.append([influencer_id, basis, rate, influencer_orders, round(total_payout, 2)])

payouts_df = pd.DataFrame(payouts, columns=["influencer_id", "basis", "rate", "orders", "total_payout"])
