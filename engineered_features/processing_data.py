import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


influencers_df = pd.read_csv('/content/influencers.csv')
posts_df = pd.read_csv('/content/posts.csv')
tracking_df = pd.read_csv('/content/tracking.csv')
payouts_df = pd.read_csv('/content/payouts.csv')

# Clean column names
for df in [influencers_df, posts_df, tracking_df, payouts_df]:
    df.columns = df.columns.str.strip()

# Fix platform column names (from PDFs: pla0orm, pla4orm)
if 'pla0orm' in posts_df.columns:
    posts_df = posts_df.rename(columns={'pla0orm': 'platform'})
if 'pla4orm' in influencers_df.columns:
    influencers_df = influencers_df.rename(columns={'pla4orm': 'platform'})

# Convert dates
posts_df['date'] = pd.to_datetime(posts_df['date'])
tracking_df['date'] = pd.to_datetime(tracking_df['date'])

print(f"✓ Loaded {len(influencers_df)} influencers")
print(f"✓ Loaded {len(posts_df)} posts")
print(f"✓ Loaded {len(tracking_df)} tracking records")
print(f"✓ Loaded {len(payouts_df)} payout records")

print("\nAggregating post metrics...")

# Aggregate posts data by influencer
posts_agg = posts_df.groupby('influencer_id').agg({
    'post_id': 'count',
    'reach': ['sum', 'mean'],
    'likes': ['sum', 'mean'],
    'comments': ['sum', 'mean'],
    'date': ['min', 'max']
}).round(2)

# Flatten column names
posts_agg.columns = ['total_posts', 'total_reach', 'avg_reach_per_post',
                     'total_likes', 'avg_likes_per_post', 'total_comments',
                     'avg_comments_per_post', 'first_post_date', 'last_post_date']

posts_agg = posts_agg.reset_index()
print(f"✓ Aggregated post metrics for {len(posts_agg)} influencers")

# Data overview
print("\nData Overview:")
print(f"Date range: {posts_df['date'].min()} to {posts_df['date'].max()}")
print(f"Platforms: {list(influencers_df['platform'].unique())}")
print(f"Categories: {list(influencers_df['category'].unique())}")

print("Aggregating business metrics...")

# Aggregate tracking data by influencer
tracking_agg = tracking_df.groupby('influencer_id').agg({
    'orders': 'sum',
    'revenue': 'sum',
    'campaign': 'nunique'
}).round(2)

tracking_agg.columns = ['total_orders', 'total_revenue', 'campaigns_count']
tracking_agg = tracking_agg.reset_index()
print(f"✓ Aggregated tracking metrics for {len(tracking_agg)} influencers")

print("Creating master dataset...")

# Start with influencers base data
master_df = influencers_df.copy()

# Merge aggregated data
master_df = master_df.merge(posts_agg, on='influencer_id', how='left')
master_df = master_df.merge(tracking_agg, on='influencer_id', how='left')
master_df = master_df.merge(payouts_df, on='influencer_id', how='left')

# Fill NAs with 0 for numeric columns
numeric_cols = ['total_posts', 'total_reach', 'total_likes', 'total_comments',
                'total_orders', 'total_revenue', 'campaigns_count', 'total_payout']
master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

print(f"✓ Created master dataset with {len(master_df)} influencers")
print(f"Master dataset shape: {master_df.shape}")

print("Calculating primary KPIs...")

# Primary KPIs
master_df['roas'] = np.where(master_df['total_payout'] > 0,
                            master_df['total_revenue'] / master_df['total_payout'], 0)

master_df['engagement_rate'] = np.where(master_df['total_reach'] > 0,
                                       (master_df['total_likes'] + master_df['total_comments']) / master_df['total_reach'] * 100, 0)

master_df['conversion_rate'] = np.where(master_df['total_reach'] > 0,
                                       master_df['total_orders'] / master_df['total_reach'] * 100, 0)

master_df['cost_per_order'] = np.where(master_df['total_orders'] > 0,
                                      master_df['total_payout'] / master_df['total_orders'], 0)

master_df['cost_per_engagement'] = np.where((master_df['total_likes'] + master_df['total_comments']) > 0,
                                            master_df['total_payout'] / (master_df['total_likes'] + master_df['total_comments']), 0)

master_df['revenue_per_post'] = np.where(master_df['total_posts'] > 0,
                                         master_df['total_revenue'] / master_df['total_posts'], 0)

# Efficiency Score (composite metric)
master_df['efficiency_score'] = np.where(
    (master_df['roas'] > 0) & (master_df['engagement_rate'] > 0) & (master_df['conversion_rate'] > 0),
    (master_df['roas'] * master_df['engagement_rate'] * master_df['conversion_rate']) / 100,
    0
)

print("✓ Calculated primary KPIs")

print("Calculating derived features...")

# Follower Tiers
def get_follower_tier(follower_count):
    if follower_count < 10000:
        return 'Nano'
    elif follower_count < 100000:
        return 'Micro'
    elif follower_count < 1000000:
        return 'Macro'
    else:
        return 'Mega'

master_df['follower_tier'] = master_df['follower_count'].apply(get_follower_tier)

# Performance Categories
def get_performance_category(roas):
    if roas >= 3.5:
        return 'High'
    elif roas >= 2.0:
        return 'Medium'
    else:
        return 'Low'

master_df['performance_category'] = master_df['roas'].apply(get_performance_category)

# Persona Combination
master_df['persona_combination'] = master_df['follower_tier'] + '+' + master_df['category'] + '+' + master_df['platform']

# ROI Score (0-100 scale)
master_df['roi_score'] = np.clip((master_df['roas'] * 10 + master_df['efficiency_score'] * 2) / 2, 0, 100)

print("✓ Calculated derived features")

print("Calculating time-based metrics...")

# Days since last post
current_date = datetime.now()
master_df['days_since_last_post'] = master_df['last_post_date'].apply(
    lambda x: (current_date - x).days if pd.notna(x) else 999
)

# Campaign duration and post frequency
master_df['campaign_duration'] = (master_df['last_post_date'] - master_df['first_post_date']).dt.days + 1
master_df['campaign_duration'] = master_df['campaign_duration'].fillna(0)

master_df['post_frequency'] = np.where(master_df['campaign_duration'] > 0,
                                      master_df['total_posts'] / master_df['campaign_duration'] * 7, 0)

# Engagement Quality & Reach Efficiency
master_df['engagement_quality'] = np.where(master_df['total_likes'] > 0,
                                          master_df['total_comments'] / master_df['total_likes'], 0)

master_df['reach_efficiency'] = np.where(master_df['follower_count'] > 0,
                                        master_df['total_reach'] / master_df['follower_count'], 0)

print("✓ Calculated time-based metrics")

print("Calculating status indicators...")

# Status based on activity and performance
def get_status(row):
    if row['days_since_last_post'] > 30:
        return 'Inactive'
    elif row['roas'] < 1.5:
        return 'Review'
    elif row['roas'] >= 3.5:
        return 'Star'
    else:
        return 'Active'

master_df['status'] = master_df.apply(get_status, axis=1)

# Investment efficiency
master_df['investment_efficiency'] = master_df['roas']  # Same as ROAS for simplicity

print("✓ Calculated status indicators")

print("Calculating performance rankings...")

# Platform performance ranking
master_df['platform_rank'] = master_df.groupby('platform')['roas'].rank(method='dense', ascending=False)

# Overall performance ranking
master_df['overall_rank'] = master_df['roas'].rank(method='dense', ascending=False)

print("✓ Calculated performance rankings")

print("Calculating executive KPIs...")

# Overall metrics
total_revenue = master_df['total_revenue'].sum()
total_payout = master_df['total_payout'].sum()
overall_roas = total_revenue / total_payout if total_payout > 0 else 0
active_campaigns = tracking_df['campaign'].nunique()
total_influencers = len(master_df)

# Best and worst performers
best_performer_idx = master_df['roas'].idxmax()
worst_performer_idx = master_df['roas'].idxmin()

executive_kpis = {
    'total_revenue': total_revenue,
    'overall_roas': overall_roas,
    'active_campaigns': active_campaigns,
    'total_influencers': total_influencers,
    'best_performer_name': master_df.loc[best_performer_idx, 'name'],
    'best_performer_roas': master_df.loc[best_performer_idx, 'roas'],
    'worst_performer_name': master_df.loc[worst_performer_idx, 'name'],
    'worst_performer_roas': master_df.loc[worst_performer_idx, 'roas']
}

print("✓ Calculated executive KPIs")

print("Creating investment action dataframes...")

# INVEST MORE: High ROAS, Low Investment
invest_more_df = master_df[
    (master_df['roas'] >= 3.5) &
    (master_df['total_payout'] <= master_df['total_payout'].quantile(0.3))
].nlargest(5, 'roas')[['name', 'roas', 'total_payout', 'total_revenue', 'platform']]

# OPTIMIZE: Low ROAS, High Investment
optimize_df = master_df[
    (master_df['roas'] < 2.0) &
    (master_df['total_payout'] >= master_df['total_payout'].quantile(0.7))
].nsmallest(5, 'roas')[['name', 'roas', 'total_payout', 'total_revenue', 'platform']]

# MONITOR: Medium Performance
monitor_df = master_df[
    (master_df['roas'] >= 2.0) & (master_df['roas'] < 3.5)
].sample(min(5, len(master_df[
    (master_df['roas'] >= 2.0) & (master_df['roas'] < 3.5)
])))[['name', 'roas', 'total_payout', 'total_revenue', 'platform']]

print("✓ Created investment action dataframes")

print("Creating aggregated insights tables...")

# Platform Performance
platform_performance = master_df.groupby('platform').agg({
    'total_revenue': 'sum',
    'total_payout': 'sum',
    'total_orders': 'sum',
    'total_reach': 'sum',
    'name': 'count'
}).rename(columns={'name': 'influencer_count'})

platform_performance['platform_roas'] = platform_performance['total_revenue'] / platform_performance['total_payout']
platform_performance['revenue_share'] = platform_performance['total_revenue'] / platform_performance['total_revenue'].sum() * 100

# Persona Performance
persona_performance = master_df.groupby('persona_combination').agg({
    'total_posts': 'sum',
    'roas': 'mean',
    'total_revenue': 'sum',
    'efficiency_score': 'mean',
    'name': 'count'
}).rename(columns={'name': 'influencer_count'}).sort_values('roas', ascending=False)

# Category Performance
category_performance = master_df.groupby('category').agg({
    'total_revenue': 'sum',
    'roas': 'mean',
    'engagement_rate': 'mean',
    'name': 'count'
}).rename(columns={'name': 'influencer_count'}).sort_values('roas', ascending=False)

# Product Performance (from tracking data)
product_performance = tracking_df.groupby('product').agg({
    'orders': 'sum',
    'revenue': 'sum'
}).sort_values('revenue', ascending=False)

print("✓ Created aggregated insights tables")

print("\n" + "="*60)
print("FINAL DATASET SUMMARY")
print("="*60)

print(f"Master DataFrame Shape: {master_df.shape}")
print(f"Columns: {list(master_df.columns)}")
print(f"\nExecutive KPIs:")
print(f"  Total Revenue: ₹{executive_kpis['total_revenue']:,.2f}")
print(f"  Overall ROAS: {executive_kpis['overall_roas']:.2f}x")
print(f"  Active Campaigns: {executive_kpis['active_campaigns']}")
print(f"  Best Performer: {executive_kpis['best_performer_name']} ({executive_kpis['best_performer_roas']:.2f}x)")
print(f"  Worst Performer: {executive_kpis['worst_performer_name']} ({executive_kpis['worst_performer_roas']:.2f}x)")

print(f"\nPlatform Distribution:")
print(master_df['platform'].value_counts())

print(f"\nPerformance Category Distribution:")
print(master_df['performance_category'].value_counts())

print(f"\nTop 5 ROAS Performers:")
print(master_df.nlargest(5, 'roas')[['name', 'platform', 'roas', 'total_revenue']].to_string(index=False))

print("\n✅ Data processing complete! Ready for Streamlit dashboard.")
