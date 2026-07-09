import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# Set wide layout and page config
st.set_page_config(
    page_title="Customer Retention & CLTV Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling for dark theme
st.markdown("""
<style>
    /* Main background and font styling */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
        font-family: 'Inter', 'Outfit', sans-serif;
    }
    
    /* Title and header accent glow */
    h1, h2, h3 {
        color: #FFFFFF;
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    .main-title {
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Metrics Card container */
    .metric-card {
        background-color: #1A1D24;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #00F2FE;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #A0AEC0;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .metric-trend {
        font-size: 0.8rem;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    /* Insights box styling */
    .insight-box {
        background: linear-gradient(135deg, #1A1D24 0%, #171923 100%);
        border-left: 4px solid #00F2FE;
        border-radius: 4px 12px 12px 4px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #1A1D24 0%, #171923 100%);
        border-left: 4px solid #00D2B4;
        border-radius: 4px 12px 12px 4px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Define paths (absolute with fallback)
BASE_DIR_DESKTOP = "C:/Users/malla.darani/OneDrive/Desktop/Customer_Retention_CLTV_Analysis/Dataset"
BASE_DIR_DOWNLOADS = "C:/Users/malla.darani/Downloads"

def find_file(filename, search_dirs):
    for d in search_dirs:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    # Fallback to local working directory
    return filename

@st.cache_data
def load_segmented_data():
    paths_to_check = [
        "C:/Users/malla.darani/OneDrive/Desktop/Customer_Retention_CLTV_Analysis/Dataset",
        "C:/Users/malla.darani/Downloads",
        "./Dataset",
        "."
    ]
    path = find_file("Segmented_cohortdataset.xlsx", paths_to_check)
    df = pd.read_excel(path)
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    # Convert CohortMonth and InvoiceMonth to strings if they are not
    df['CohortMonth'] = df['CohortMonth'].astype(str)
    df['InvoiceMonth'] = df['InvoiceMonth'].astype(str)
    return df

@st.cache_resource
def load_excel_summary(filename):
    paths_to_check = [
        "C:/Users/malla.darani/Downloads",
        "C:/Users/malla.darani/OneDrive/Desktop/Customer_Retention_CLTV_Analysis/Dataset",
        "."
    ]
    path = find_file(filename, paths_to_check)
    if os.path.exists(path):
        return pd.ExcelFile(path)
    return None

# Load the primary dataset
try:
    with st.spinner("Loading transaction datasets (210,716 rows) into memory..."):
        df = load_segmented_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading main dataset: {e}")
    data_loaded = False

# Sidebar Navigation and Filters
st.sidebar.markdown("<h2 style='text-align: center; color: #00F2FE;'>🧭 Navigation</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("Go to Page:", [
    "🏠 Executive Overview",
    "📈 Sales Analytics",
    "👥 Customer Analytics",
    "📅 Cohort & Retention Analysis",
    "💎 CLTV Dashboard",
    "💡 Business Insights & recommendations"
])

if data_loaded:
    # Sidebar Filters
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Global Filters")
    
    # 1. Country Filter
    countries = sorted(list(df['Country'].unique()))
    selected_countries = st.sidebar.multiselect("Select Countries", countries, default=countries)
    
    # 2. Month Filter
    months = sorted(list(df['InvoiceMonth'].unique()))
    selected_months = st.sidebar.multiselect("Select Months", months, default=months)
    
    # 3. Customer ID Filter (Text Search for performance)
    customer_query = st.sidebar.text_input("Search Customer ID (Numeric)", "")

    # Apply filters dynamically
    filtered_df = df.copy()
    if selected_countries:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
    if selected_months:
        filtered_df = filtered_df[filtered_df['InvoiceMonth'].isin(selected_months)]
    if customer_query.strip():
        try:
            cust_id = int(customer_query.strip())
            filtered_df = filtered_df[filtered_df['CustomerID'] == cust_id]
        except ValueError:
            st.sidebar.warning("Please enter a valid numeric Customer ID.")

    # Calculate dynamic filtered KPIs
    total_rev = filtered_df['Revenue'].sum()
    total_custs = filtered_df['CustomerID'].nunique()
    total_ords = filtered_df['InvoiceNo'].nunique()
    aov = total_rev / total_ords if total_ords > 0 else 0
    purchase_freq = total_ords / total_custs if total_custs > 0 else 0
    cltv_val = aov * purchase_freq
    
    # Repeat Customer Rate (Retention Rate)
    if total_custs > 0:
        orders_per_cust = filtered_df.groupby('CustomerID')['InvoiceNo'].nunique()
        repeat_custs = (orders_per_cust > 1).sum()
        retention_rate = repeat_custs / total_custs
    else:
        retention_rate = 0

# --- PAGE 1: EXECUTIVE OVERVIEW ---
if page == "🏠 Executive Overview":
    st.markdown("<h1 class='main-title'>Cohort Retention & CLTV Analysis Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>E-Commerce Customer Performance & Lifetime Value Analytics (Online Retail Dataset)</p>", unsafe_allow_html=True)
    
    if not data_loaded:
        st.warning("Please verify data source configuration.")
    else:
        # Display Premium KPI Cards
        kpi_cols = st.columns(7)
        
        metrics = [
            ("Total Revenue", f"${total_rev:,.2f}", "#00F2FE", "Overall Sales Value"),
            ("Total Customers", f"{total_custs:,}", "#4FACFE", "Unique Shoppers"),
            ("Total Orders", f"{total_ords:,}", "#00D2B4", "Completed Invoices"),
            ("Average Order Value", f"${aov:,.2f}", "#A18CD1", "Avg Spent Per Order"),
            ("Purchase Frequency", f"{purchase_freq:.2f}", "#FAD0C4", "Avg Orders/Customer"),
            ("Customer Lifetime Value", f"${cltv_val:,.2f}", "#FF0844", "Avg Customer Worth"),
            ("Retention Rate", f"{retention_rate*100:.2f}%", "#F9D423", "Repeat Shopper Rate")
        ]
        
        for col, (label, val, color, desc) in zip(kpi_cols, metrics):
            with col:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>{label}</div>
                    <div class='metric-value' style='color: {color};'>{val}</div>
                    <div class='metric-trend' style='color: #A0AEC0;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabs for Project Deliverables and Overview
        tab1, tab2, tab3 = st.tabs(["📋 Project Overview", "🗓️ Weekly Milestones", "📦 Project Deliverables"])
        
        with tab1:
            st.markdown("""
            ### 📌 Project Background & Objectives
            This project focuses on translating raw transactional data from the **Online Retail Dataset** into actionable growth strategies. 
            Instead of examining metrics in isolation, we model customer purchase behavior to answer business-critical questions:
            - **Who are our most valuable customers?** (Customer Lifetime Value modeling)
            - **Do customers return over time?** (Cohort Cohort-Index Retention analysis)
            - **How do customer behavior dynamics vary by region?** (Segment-wise AOV and Purchase Frequency mapping)
            
            ### 🚀 Strategic Significance
            Retaining an existing customer is **5x cheaper** than acquiring a new one. By identifying the churn inflection points (where customers drop off) and mapping the CLTV of different regional segments, businesses can allocate marketing budgets efficiently and craft targeted communication to maximize long-term loyalty.
            """)
            
        with tab2:
            xl_summary = load_excel_summary("Final_Project_Summary.xlsx")
            if xl_summary is not None:
                try:
                    df_week = xl_summary.parse("Week Summary")
                    st.table(df_week)
                except:
                    st.info("Week summary details are loaded in the background.")
            else:
                # Fallback week description
                st.markdown("""
                - **Week 1: Data Cleaning & Preprocessing**: Removed cancelled transactions (InvoiceNo starting with C), deleted missing CustomerIDs, handled outliers in quantities and unit prices, and calculated initial revenue.
                - **Week 2: Cohort & Customer Analytics**: Developed the Cohort Retention Matrix (1-24 months index) to analyze customer decay, computed repeat purchase rates, and analyzed monthly revenue trends.
                - **Week 3: Segmentation & CLTV Modeling**: Segmented customers into geographic groups (UK, Europe, Other). Computed key parameters (Average Order Value, Purchase Frequency) to model Historical CLTV.
                - **Week 4: Business Insights & Dashboards**: Built rule-based business decision recommendations, formulated priority action frameworks, and consolidated deliverables.
                """)
                
        with tab3:
            xl_summary = load_excel_summary("Final_Project_Summary.xlsx")
            if xl_summary is not None:
                try:
                    df_del = xl_summary.parse("Project Deliverables")
                    st.dataframe(df_del, use_container_width=True)
                except:
                    st.info("Deliverables list loaded.")
            else:
                st.markdown("""
                | Deliverable | Description | Outcome |
                |---|---|---|
                | **Data Preprocessing Pipeline** | Standardized ingestion and outlier removal | Cleaned dataset containing only positive quantities/prices |
                | **Cohort Retention Matrix** | 24-month retention grid | Pinpointed drop-off rates at Months 2-3 |
                | **CLTV Analytics Framework** | Formula-based modeling of lifetime value | Discovered high CLTV in Europe/Other segments |
                | **Business Insights Engine** | Automated rule generation for segment targeting | Identified UK as high volume but low CLTV |
                """)

# --- PAGE 2: SALES ANALYTICS ---
elif page == "📈 Sales Analytics":
    st.markdown("<h1 class='main-title'>Sales & Revenue Performance</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Revenue Trends, Regional Contributions, and Product Metrics</p>", unsafe_allow_html=True)
    
    if data_loaded:
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. Monthly Revenue Trend
            st.markdown("### 📅 Monthly Revenue Trend")
            df_monthly = filtered_df.groupby('InvoiceMonth')['Revenue'].sum().reset_index()
            # Sort chronologically
            df_monthly['DateTemp'] = pd.to_datetime(df_monthly['InvoiceMonth'] + "-01")
            df_monthly = df_monthly.sort_values('DateTemp')
            
            fig_trend = px.line(
                df_monthly,
                x='InvoiceMonth',
                y='Revenue',
                markers=True,
                labels={'Revenue': 'Revenue ($)', 'InvoiceMonth': 'Month'},
                template="plotly_dark",
                color_discrete_sequence=['#00F2FE']
            )
            fig_trend.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_gridcolor='#2D3748',
                yaxis_gridcolor='#2D3748'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col2:
            # 2. Country Revenue Contribution
            st.markdown("### 🌍 Top Countries by Revenue")
            df_country = filtered_df.groupby('Country')['Revenue'].sum().reset_index()
            df_country = df_country.sort_values('Revenue', ascending=False).head(10)
            
            fig_pie = px.pie(
                df_country,
                names='Country',
                values='Revenue',
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.sequential.Blugrn
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # Product Sales
        st.markdown("### 📦 Top 10 Best-Selling Products (by Revenue)")
        df_prod = filtered_df.groupby('Description')['Revenue'].sum().reset_index()
        df_prod = df_prod.sort_values('Revenue', ascending=False).head(10)
        
        fig_prod = px.bar(
            df_prod,
            x='Revenue',
            y='Description',
            orientation='h',
            labels={'Revenue': 'Revenue ($)', 'Description': 'Product'},
            template="plotly_dark",
            color='Revenue',
            color_continuous_scale='tealgrn'
        )
        fig_prod.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis={'categoryorder': 'total ascending'},
            xaxis_gridcolor='#2D3748'
        )
        st.plotly_chart(fig_prod, use_container_width=True)

# --- PAGE 3: CUSTOMER ANALYTICS ---
elif page == "👥 Customer Analytics":
    st.markdown("<h1 class='main-title'>Customer In-Depth Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Top Customers, Order Frequencies, and Individual Profile Exploration</p>", unsafe_allow_html=True)
    
    if data_loaded:
        tab_overall, tab_lookup = st.tabs(["👥 Overall Customer Metrics", "🔍 Individual Customer Profile"])
        
        with tab_overall:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top Customers by Revenue
                st.markdown("### 🏆 Top 10 Customers by Revenue Contribution")
                df_cust_rev = filtered_df.groupby('CustomerID')['Revenue'].sum().reset_index()
                df_cust_rev = df_cust_rev.sort_values('Revenue', ascending=False).head(10)
                # Format IDs
                df_cust_rev['CustomerID'] = df_cust_rev['CustomerID'].astype(str)
                
                fig_cust = px.bar(
                    df_cust_rev,
                    x='CustomerID',
                    y='Revenue',
                    labels={'Revenue': 'Spend ($)', 'CustomerID': 'Customer ID'},
                    template="plotly_dark",
                    color='Revenue',
                    color_continuous_scale='Blues'
                )
                fig_cust.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_gridcolor='#2D3748'
                )
                st.plotly_chart(fig_cust, use_container_width=True)
                
            with col2:
                # Distribution of Orders
                st.markdown("### 📦 Customer Order Frequency Distribution")
                df_cust_ords = filtered_df.groupby('CustomerID')['InvoiceNo'].nunique().reset_index()
                
                # Cap outliers for better viz
                q_99 = df_cust_ords['InvoiceNo'].quantile(0.99)
                df_cust_ords_filtered = df_cust_ords[df_cust_ords['InvoiceNo'] <= q_99]
                
                fig_dist = px.histogram(
                    df_cust_ords_filtered,
                    x='InvoiceNo',
                    nbins=30,
                    labels={'InvoiceNo': 'Number of Orders'},
                    template="plotly_dark",
                    color_discrete_sequence=['#4FACFE']
                )
                fig_dist.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_gridcolor='#2D3748',
                    yaxis_gridcolor='#2D3748'
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
        with tab_lookup:
            st.markdown("### 🔍 Customer ID Detailed Profile")
            cust_list = sorted(list(df['CustomerID'].unique()))
            # Convert float to integer if they have decimals
            selected_cust = st.selectbox("Select Customer ID to Profile", cust_list)
            
            cust_df = df[df['CustomerID'] == selected_cust]
            
            if len(cust_df) > 0:
                c_rev = cust_df['Revenue'].sum()
                c_ords = cust_df['InvoiceNo'].nunique()
                c_aov = c_rev / c_ords if c_ords > 0 else 0
                c_country = cust_df['Country'].iloc[0]
                c_segment = cust_df['RegionSegment'].iloc[0]
                c_first = cust_df['CohortMonth'].iloc[0]
                c_items = len(cust_df)
                
                c_col1, c_col2, c_col3, c_col4 = st.columns(4)
                
                with c_col1:
                    st.metric("Total Spent", f"${c_rev:,.2f}")
                    st.metric("Country", str(c_country))
                with c_col2:
                    st.metric("Total Orders", f"{c_ords}")
                    st.metric("Segment", str(c_segment))
                with c_col3:
                    st.metric("Average Order Value (AOV)", f"${c_aov:,.2f}")
                    st.metric("Cohort Month", str(c_first))
                with c_col4:
                    st.metric("Total Items Purchased", f"{c_items}")
                
                st.markdown("#### 🛒 Product Purchase Details")
                st.dataframe(
                    cust_df[['InvoiceNo', 'InvoiceDate', 'Description', 'Quantity', 'UnitPrice', 'Revenue']].sort_values('InvoiceDate', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("Please select a customer from the dropdown to display their profile details.")

# --- PAGE 4: COHORT & RETENTION ANALYSIS ---
elif page == "📅 Cohort & Retention Analysis":
    st.markdown("<h1 class='main-title'>Cohort & Retention Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Cohort Active Customer Matrices and Decay/Survival Curve Benchmarking</p>", unsafe_allow_html=True)
    
    if data_loaded:
        st.markdown("### 🌡️ Cohort Retention Matrix Heatmap")
        
        # Calculate Cohort Index
        df_cohort = filtered_df.copy()
        df_cohort['InvoiceMonth_dt'] = pd.to_datetime(df_cohort['InvoiceMonth'] + "-01")
        df_cohort['CohortMonth_dt'] = pd.to_datetime(df_cohort['CohortMonth'] + "-01")
        
        df_cohort['CohortIndex'] = (
            (df_cohort['InvoiceMonth_dt'].dt.year - df_cohort['CohortMonth_dt'].dt.year) * 12
            + (df_cohort['InvoiceMonth_dt'].dt.month - df_cohort['CohortMonth_dt'].dt.month)
            + 1
        )
        
        cohort_counts = df_cohort.groupby(['CohortMonth', 'CohortIndex'])['CustomerID'].nunique().reset_index()
        cohort_matrix = cohort_counts.pivot(index='CohortMonth', columns='CohortIndex', values='CustomerID')
        
        # Calculate retention rate
        cohort_size = cohort_matrix.iloc[:, 0]
        retention_matrix = cohort_matrix.divide(cohort_size, axis=0)
        
        # Drop Month 1 which is always 100% for plotting colors, or plot all
        # To make it readable, let's plot all but format as percentage
        z_vals = retention_matrix.values
        x_vals = list(retention_matrix.columns)
        y_vals = list(retention_matrix.index)
        
        # Create text annotations
        text_matrix = []
        for i in range(len(y_vals)):
            row_txt = []
            for j in range(len(x_vals)):
                val = z_vals[i][j]
                if pd.isna(val):
                    row_txt.append("")
                else:
                    row_txt.append(f"{val*100:.1f}%")
            text_matrix.append(row_txt)
            
        fig_heat = go.Figure(data=go.Heatmap(
            z=z_vals,
            x=x_vals,
            y=y_vals,
            text=text_matrix,
            texttemplate="%{text}",
            colorscale='YlGnBu',
            showscale=True,
            colorbar=dict(title="Retention Rate", tickformat=".0%")
        ))
        
        fig_heat.update_layout(
            template="plotly_dark",
            title="Cohort Retention Rates (%)",
            xaxis_title="Cohort Month Index (Month 1 = Signup)",
            yaxis_title="Cohort Month Group",
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Retention Decay line chart
        st.markdown("### 📉 Cohort Retention Decay Curve")
        # Average retention rates across all cohorts
        avg_retention = retention_matrix.mean().reset_index()
        avg_retention.columns = ['CohortIndex', 'RetentionRate']
        # Remove Index 1 since it's 100%
        avg_retention_decay = avg_retention[avg_retention['CohortIndex'] > 1]
        
        fig_decay = px.line(
            avg_retention_decay,
            x='CohortIndex',
            y='RetentionRate',
            markers=True,
            labels={'CohortIndex': 'Month Index', 'RetentionRate': 'Avg Retention Rate'},
            template="plotly_dark",
            color_discrete_sequence=['#FF0844']
        )
        fig_decay.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_tickformat='.1%',
            xaxis_gridcolor='#2D3748',
            yaxis_gridcolor='#2D3748'
        )
        st.plotly_chart(fig_decay, use_container_width=True)
        
        # Display insights summary
        st.markdown("""
        <div class='insight-box'>
            <h4>🔍 Key Cohort Findings</h4>
            <ul>
                <li><b>Month 2 Churn Inflection Point:</b> The steepest drop-off occurs between Month 1 and Month 2. Overall retention drops below 20% by Month 3 across most cohorts.</li>
                <li><b>NPS Inflection:</b> Certain holiday cohorts (e.g. 2010-12) exhibit stronger retention curves, indicating that promotion-acquired cohorts may have distinct long-term behaviors.</li>
                <li><b>Retention Action Window:</b> Customer retention initiatives must target users within <b>30 days</b> of their first transaction to mitigate the high drop-off.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE 5: CLTV DASHBOARD ---
elif page == "💎 CLTV Dashboard":
    st.markdown("<h1 class='main-title'>Customer Lifetime Value (CLTV) Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Segment Metrics, AOV vs. Purchase Frequency, and Rank Contributions</p>", unsafe_allow_html=True)
    
    xl_kpi = load_excel_summary("Business_KPI_Dashboard.xlsx")
    if xl_kpi is not None:
        try:
            df_kpi = xl_kpi.parse("Sheet1")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏆 Historical CLTV by Region Segment")
                fig_cltv_reg = px.bar(
                    df_kpi,
                    x='RegionSegment',
                    y='Historical_CLTV',
                    labels={'Historical_CLTV': 'Historical CLTV ($)', 'RegionSegment': 'Region Segment'},
                    template="plotly_dark",
                    color='Historical_CLTV',
                    color_continuous_scale='Purples'
                )
                fig_cltv_reg.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_gridcolor='#2D3748'
                )
                st.plotly_chart(fig_cltv_reg, use_container_width=True)
                
            with col2:
                st.markdown("### 💰 Total Revenue by Region Segment")
                fig_rev_reg = px.bar(
                    df_kpi,
                    x='RegionSegment',
                    y='Total_Revenue',
                    labels={'Total_Revenue': 'Total Revenue ($)', 'RegionSegment': 'Region Segment'},
                    template="plotly_dark",
                    color='Total_Revenue',
                    color_continuous_scale='Teal'
                )
                fig_rev_reg.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_gridcolor='#2D3748'
                )
                st.plotly_chart(fig_rev_reg, use_container_width=True)
                
            # Bubble Chart mapping AOV, Purchase Frequency, and Customer Count
            st.markdown("### 🔮 Segment Value Quadrant (AOV vs. Purchase Frequency)")
            fig_bubble = px.scatter(
                df_kpi,
                x='Average_Order_Value',
                y='Purchase_Frequency',
                size='Total_Customers',
                color='RegionSegment',
                hover_name='RegionSegment',
                labels={'Average_Order_Value': 'Average Order Value ($)', 'Purchase_Frequency': 'Purchase Frequency'},
                template="plotly_dark",
                text='RegionSegment'
            )
            fig_bubble.update_traces(textposition='top center')
            fig_bubble.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_gridcolor='#2D3748',
                yaxis_gridcolor='#2D3748',
                height=500
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
            
            # Show the precomputed rank table
            st.markdown("### 📊 Segment Performance Ledger")
            st.dataframe(df_kpi, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error parsing KPI dashboard sheet: {e}")
    else:
        st.info("Please verify the presence of 'Business_KPI_Dashboard.xlsx' in Downloads to display regional segment metrics.")

# --- PAGE 6: BUSINESS INSIGHTS & RECOMMENDATIONS ---
elif page == "💡 Business Insights & recommendations":
    st.markdown("<h1 class='main-title'>Business Insights & Decision Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Precomputed Strategic Insights, Priority Rules, and Automated Recommendations</p>", unsafe_allow_html=True)
    
    xl_insights = load_excel_summary("Executive_Business_Insights.xlsx")
    xl_decisions = load_excel_summary("Business_Decision_Recommendations.xlsx")
    
    tab_insights, tab_decisions = st.tabs(["💡 Executive Summary & Insights", "⚙️ Rule-Based Decision Engine"])
    
    with tab_insights:
        if xl_insights is not None:
            try:
                df_summary = xl_insights.parse("Executive Summary")
                df_insights = xl_insights.parse("Business Insights")
                df_recs = xl_insights.parse("Recommendations")
                
                col_sum, col_ins = st.columns(2)
                
                with col_sum:
                    st.markdown("### 🏆 Regional Leaderboard")
                    st.table(df_summary)
                    
                with col_ins:
                    st.markdown("### 💡 Core Findings")
                    for idx, row in df_insights.iterrows():
                        st.markdown(f"""
                        <div class='insight-box'>
                            <b>Insight {idx+1}: {row['Business Insight']}</b><br>
                            <span style='color: #A0AEC0; font-size: 0.9rem;'>Impact: {row['Business Impact']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                st.markdown("### 🎯 Strategic Growth Recommendations")
                for idx, row in df_recs.iterrows():
                    st.markdown(f"""
                    <div class='recommendation-box'>
                        <b>Strategy {idx+1}</b><br>
                        {row['Recommendations']}
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error parsing insights sheets: {e}")
        else:
            st.info("Insights file not found. Here are the core insights:")
            st.markdown("""
            - **UK Segment**: Represents over 80% of transaction volumes, but records the lowest Average Order Value (AOV = $411).
            - **Other Segment**: Achieved the highest Historical CLTV ($3,630) due to high AOV ($1,093).
            - **Retention Rates**: The steepest customer churn occurs in Month 2. High priority action is needed.
            """)
            
    with tab_decisions:
        if xl_decisions is not None:
            try:
                df_dec = xl_decisions.parse("Decision Report")
                
                st.markdown("### ⚙️ Priority Action Matrix")
                # Add priority filter in dashboard
                priority_filter = st.selectbox("Filter Recommendations by Priority", ["All", "High", "Medium"])
                
                if priority_filter != "All":
                    filtered_dec = df_dec[df_dec['Priority'] == priority_filter]
                else:
                    filtered_dec = df_dec
                    
                st.dataframe(filtered_dec, use_container_width=True)
                
                # Summary card counts
                sum_col1, sum_col2 = st.columns(2)
                with sum_col1:
                    high_p = len(df_dec[df_dec['Priority'] == 'High'])
                    st.metric("High Priority Action Points", f"{high_p}")
                with sum_col2:
                    avg_impact = df_dec['Historical_CLTV'].mean()
                    st.metric("Benchmark Lifetime Value", f"${avg_impact:,.2f}")
                    
            except Exception as e:
                st.error(f"Error parsing decision recommendations: {e}")
        else:
            st.info("Decision recommendations sheet not found.")
