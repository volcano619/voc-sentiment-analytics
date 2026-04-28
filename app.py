"""
Streamlit Dashboard for Voice of Customer Analytics

Features:
1. Real-time sentiment analysis
2. Business metrics dashboard (NPS, CSAT, Churn)
3. Aspect-based analysis
4. Action queue for customer success
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import logging

from config import (
    APP_TITLE, APP_LAYOUT, TARGET_NPS, TARGET_CSAT,
    ASPECTS, SENTIMENT_LABELS
)
from models.preprocessing import load_feedback_data, generate_synthetic_dataset, clean_text
from models.sentiment import SentimentAnalyzer
from models.aspect import AspectExtractor, AspectSentimentAnalyzer
from models.business_metrics import BusinessMetricsCalculator, DashboardMetrics
import shared_ui

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title=APP_TITLE,
    layout=APP_LAYOUT,
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# Apply global theme
shared_ui.apply_global_theme()

# Custom project-specific CSS extensions
st.markdown("""
<style>
    .nps-promoter { color: #10B981; font-weight: 700; }
    .nps-passive { color: #F59E0B; font-weight: 700; }
    .nps-detractor { color: #EF4444; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# INITIALIZATION
# ============================================================================

@st.cache_resource
def get_analyzer():
    """Initialize and cache the sentiment analyzer."""
    return SentimentAnalyzer(model_type="auto")


@st.cache_resource  
def get_aspect_analyzer(_sentiment_analyzer):
    """Initialize aspect sentiment analyzer."""
    return AspectSentimentAnalyzer(_sentiment_analyzer)


@st.cache_data
def load_data():
    """Load or generate feedback data."""
    return load_feedback_data()


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Data refresh
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Target settings
    st.markdown("### 🎯 Business Targets")
    
    if "target_nps" not in st.session_state:
        st.session_state.target_nps = TARGET_NPS
    if "target_csat" not in st.session_state:
        st.session_state.target_csat = TARGET_CSAT
        
    target_nps = st.number_input("Target NPS", key="target_nps", min_value=-100, max_value=100)
    target_csat = st.number_input("Target CSAT", key="target_csat", min_value=1.0, max_value=5.0, step=0.1)
    
    st.markdown("---")
    st.markdown("### 📊 Model Info")
    analyzer = get_analyzer()
    st.markdown(f"- **Model**: {analyzer.model_type}")
    st.markdown("- **Classes**: 5 (Very Neg → Very Pos)")
    st.markdown("- **Aspects**: 6 categories")


# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
shared_ui.add_header(
    "🎯 Voice of Customer Analytics",
    "AI-powered sentiment analysis with business metrics focus | *Reducing the $75B annual cost of poor customer experience*"
)

# Load data and analyzer
data = load_data()
analyzer = get_analyzer()
aspect_analyzer = get_aspect_analyzer(analyzer)

st.markdown("---")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Dashboard",
    "💬 Analyze Text",
    "📈 NPS & CSAT",
    "🎯 Aspect Analysis",
    "🚨 Action Queue"
])


# ============================================================================
# TAB 1: EXECUTIVE DASHBOARD
# ============================================================================

with tab1:
    st.markdown("### Executive Summary - Customer Health Overview")
    
    # Run analysis on all data
    with st.spinner("Analyzing customer feedback..."):
        results = [aspect_analyzer.analyze(d["text"]) for d in data]
        
        # Enrich with customer IDs
        for i, r in enumerate(results):
            r["customer_id"] = data[i]["customer_id"]
    
    # Get executive summary
    dashboard = DashboardMetrics(results, target_nps=target_nps, target_csat=target_csat)
    summary = dashboard.get_executive_summary()
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        shared_ui.create_metric_card("Net Promoter Score", f"{summary['nps']['nps']:+.0f}", delta=f"{summary['nps']['vs_target']:+.0f} vs target")
    with col2:
        shared_ui.create_metric_card("Customer Satisfaction", f"{summary['csat']['csat']:.2f}/5", delta=f"{summary['csat']['vs_target']:+.2f} vs target")
    with col3:
        shared_ui.create_metric_card("Avg Churn Risk", f"{summary['churn']['average_risk']:.0%}", delta=f"{summary['churn']['high_risk_count']} high risk", delta_pos=False)
    with col4:
        shared_ui.create_metric_card("Urgent Actions", str(summary['urgent_actions']), delta="P0/P1 priority", delta_pos=False if summary['urgent_actions'] > 0 else True)
    
    st.markdown(f"**Overall Health:** {summary['summary']['overall_health']}")
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Sentiment Distribution")
        dist = summary["sentiment_distribution"]
        fig = px.pie(
            values=list(dist.values()),
            names=list(dist.keys()),
            color_discrete_sequence=['#EF4444', '#F59E0B', '#94A3B8', '#10B981', '#059669']
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### NPS Breakdown")
        nps_data = summary["nps"]
        fig = go.Figure(go.Bar(
            x=['Promoters', 'Passives', 'Detractors'],
            y=[nps_data['promoters_pct'], nps_data['passives_pct'], nps_data['detractors_pct']],
            marker_color=['#10B981', '#F59E0B', '#EF4444'],
            text=[f"{nps_data['promoters_pct']}%", f"{nps_data['passives_pct']}%", f"{nps_data['detractors_pct']}%"],
            textposition='auto'
        ))
        fig.update_layout(height=300, yaxis_title="Percentage")
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# TAB 2: ANALYZE TEXT
# ============================================================================

with tab2:
    st.markdown("### Real-time Sentiment Analysis")
    
    # Text input
    user_text = st.text_area(
        "Enter customer feedback to analyze:",
        placeholder="e.g., 'The product quality is terrible and customer support was no help at all!'",
        height=100
    )
    
    if st.button("Analyze Sentiment", type="primary") or user_text:
        if user_text:
            result = aspect_analyzer.analyze(user_text)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### Sentiment")
                
                sentiment = result["sentiment"]
                color_map = {
                    "Very Negative": "🔴", "Negative": "🟠",
                    "Neutral": "⚪", "Positive": "🟢", "Very Positive": "💚"
                }
                
                st.markdown(f"### {color_map.get(sentiment, '⚪')} {sentiment}")
                st.progress(result["confidence"])
                st.caption(f"Confidence: {result['confidence']:.1%}")
            
            with col2:
                st.markdown("#### Business Impact")
                # Metrics cards for business impact
                shared_ui.create_metric_card("Churn Risk", f"{result['churn_risk']:.0%}", delta=result['priority'], delta_pos=False if result['churn_risk'] > 0.5 else True)
                shared_ui.create_metric_card("Predicted NPS", f"{result['predicted_nps']}/10", delta="Likely score")
                st.info(f"**Recommendation:** {result['recommended_action']}")
            
            st.markdown("---")
            st.markdown("#### Aspect Analysis")
            st.markdown(result["aspect_summary"])
            st.markdown(f"**Primary Aspect:** {result['primary_aspect'].replace('_', ' ').title()}")
    else:
        st.info("Enter customer feedback above to analyze sentiment and business impact")


# ============================================================================
# TAB 3: NPS & CSAT TRENDS
# ============================================================================

with tab3:
    st.markdown("### NPS & CSAT Analytics")
    
    # Analyze all data if not already done
    if 'results' not in dir() or not results:
        results = [aspect_analyzer.analyze(d["text"]) for d in data]
    
    calculator = BusinessMetricsCalculator(target_nps=target_nps, target_csat=target_csat)
    nps_metrics = calculator.calculate_nps(results)
    csat_metrics = calculator.calculate_csat(results)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Net Promoter Score (NPS)")
        
        # NPS gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=nps_metrics["nps"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "NPS"},
            delta={'reference': target_nps},
            gauge={
                'axis': {'range': [-100, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [-100, 0], 'color': "#FEE2E2"},
                    {'range': [0, 50], 'color': "#FEF3C7"},
                    {'range': [50, 100], 'color': "#D1FAE5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': target_nps
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        - <span class="nps-promoter">Promoters (9-10):</span> {nps_metrics['promoters']} ({nps_metrics['promoters_pct']}%)
        - <span class="nps-passive">Passives (7-8):</span> {nps_metrics['passives']} ({nps_metrics['passives_pct']}%)
        - <span class="nps-detractor">Detractors (0-6):</span> {nps_metrics['detractors']} ({nps_metrics['detractors_pct']}%)
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Customer Satisfaction (CSAT)")
        
        # CSAT distribution
        fig = px.bar(
            x=['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
            y=[csat_metrics['distribution'].get(i, 0) for i in range(1, 6)],
            color=['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
            color_discrete_sequence=['#EF4444', '#F59E0B', '#94A3B8', '#10B981', '#059669']
        )
        fig.update_layout(height=300, showlegend=False, yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
        
        shared_ui.create_metric_card("Average CSAT", f"{csat_metrics['csat']:.2f}/5", delta=f"{csat_metrics['vs_target']:+.2f} vs target")
        st.markdown(f"**Satisfied (4-5 stars):** {csat_metrics['satisfied_pct']}%")


# ============================================================================
# TAB 4: ASPECT ANALYSIS
# ============================================================================

with tab4:
    st.markdown("### Aspect-Based Sentiment Analysis")
    st.markdown("*Identify which business areas need attention*")
    
    # Get aspect breakdown
    aspect_breakdown = aspect_analyzer.get_aspect_breakdown(results)
    
    # Get aspect breakdown
    aspect_breakdown = aspect_analyzer.get_aspect_breakdown(results)
    
    # Create Heatmap Data
    aspects_list = list(aspect_breakdown.keys())
    sentiment_cats = ["Positive", "Neutral", "Negative"]
    
    z_data = []
    for aspect in aspects_list:
        counts = aspect_breakdown[aspect]["counts"]
        total = aspect_breakdown[aspect]["total"]
        z_data.append([
            counts["positive"] / total * 100,
            counts["neutral"] / total * 100,
            counts["negative"] / total * 100
        ])
    
    # Display Heatmap
    st.markdown("#### Aspect-Sentiment Heatmap (%)")
    fig = px.imshow(
        z_data,
        labels=dict(x="Sentiment", y="Aspect", color="Percentage"),
        x=sentiment_cats,
        y=[a.replace('_', ' ').title() for a in aspects_list],
        color_continuous_scale='RdYlGn',
        text_auto=".1f",
        aspect="auto"
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed stats in cards
    cols = st.columns(3)
    for i, aspect in enumerate(aspects_list):
        metrics = aspect_breakdown[aspect]
        with cols[i % 3]:
            st.markdown(f"**{aspect.replace('_', ' ').title()}**")
            st.markdown(f"Status: {metrics['status']}")
            st.markdown(f"Health Score: {metrics['health_score']}")
            st.markdown("---")


# ============================================================================
# TAB 5: ACTION QUEUE
# ============================================================================

with tab5:
    st.markdown("### Customer Success Action Queue")
    st.markdown("*Prioritized by business impact and churn risk*")
    
    # Get action queue
    action_queue = calculator.generate_action_queue(results)
    
    if not action_queue:
        st.success("🎉 No urgent actions required! Customer health is good.")
    else:
        st.warning(f"⚠️ {len(action_queue)} customers need attention")
        
        # Convert to dataframe for display
        df = pd.DataFrame(action_queue)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            priority_filter = st.multiselect(
                "Filter by Priority",
                options=["P0", "P1", "P2", "P3"],
                default=["P0", "P1"]
            )
        with col2:
            aspect_filter = st.multiselect(
                "Filter by Aspect",
                options=df["aspect"].unique().tolist(),
                default=[]
            )
        
        # Apply filters
        filtered_df = df[df["priority"].isin(priority_filter)]
        if aspect_filter:
            filtered_df = filtered_df[filtered_df["aspect"].isin(aspect_filter)]
        
        # Display
        for _, row in filtered_df.iterrows():
            with st.expander(f"{row['urgency']} {row['customer_id']} - {row['sentiment']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Feedback:** {row['text_preview']}")
                    st.markdown(f"**Aspect:** {row['aspect'].replace('_', ' ').title()}")
                
                with col2:
                    st.markdown(f"**Churn Risk:** {row['churn_risk']:.0%}")
                    st.markdown(f"**Action:** {row['recommended_action']}")


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    🎯 Voice of Customer Analytics | AI-Powered Business Intelligence<br>
    <em>Helping reduce the $75B annual cost of poor customer experience</em>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.875rem; padding: 2rem 0;">
    🎯 Voice of Customer Analytics | Built with Transformers + Aspect-Based SA<br>
    <span style="font-family: 'Roboto Mono', monospace;">Version 1.4.0-Premium</span>
</div>
""", unsafe_allow_html=True)
