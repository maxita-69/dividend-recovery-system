"""
Pattern Analysis - Analisi Pattern Pre-Dividendo → Recovery Post-Dividendo

Trova correlazioni tra comportamento PRE-dividendo e recovery POST-dividendo
per identificare segnali predittivi.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Stock, Dividend
from src.utils.pattern_analysis import analyze_all_dividends, find_correlations, find_similar_patterns
from src.utils import get_database_session, get_logger, OperationLogger
from config import get_config

logger = get_logger(__name__)
cfg = get_config()

st.set_page_config(
    page_title="Pattern Analysis",
    page_icon="🔍",
    layout="wide"
)

# ============================================================================
# AUTHENTICATION - Must be after set_page_config
# ============================================================================
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_authentication

require_authentication()


# ============================================================================
# FUNZIONI UI
# ============================================================================

@st.cache_resource
def get_session():
    """Get database session (cached)."""
    return get_database_session()


def create_correlation_heatmap(correlations_df):
    """Create interactive heatmap of correlations."""
    if correlations_df.empty:
        st.warning("⚠️ Nessuna correlazione significativa trovata")
        return

    # Pivot per creare matrice
    # Pre-features on Y-axis, post-metrics on X-axis
    pivot = correlations_df.pivot_table(
        index='pre_feature',
        columns='post_metric',
        values='correlation',
        aggfunc='first'
    )

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=pivot.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlazione")
    ))

    fig.update_layout(
        title="Correlazioni: Features Pre-Dividendo vs Recovery Post-Dividendo",
        xaxis_title="Metriche Post-Dividendo",
        yaxis_title="Features Pre-Dividendo",
        height=max(400, len(pivot.index) * 25),
        xaxis={'side': 'top'}
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_scatter_correlation(df, pre_feature, post_metric):
    """Plot scatter of specific pre-feature vs post-metric."""
    if pre_feature not in df.columns or post_metric not in df.columns:
        st.error(f"Colonne non trovate: {pre_feature}, {post_metric}")
        return

    # Calculate correlation
    corr = df[[pre_feature, post_metric]].corr().iloc[0, 1]

    fig = px.scatter(
        df,
        x=pre_feature,
        y=post_metric,
        trendline="ols",
        title=f"{pre_feature} vs {post_metric} (r = {corr:.3f})",
        labels={pre_feature: pre_feature.replace('_', ' '),
                post_metric: post_metric.replace('_', ' ')},
        hover_data=['ex_date', 'dividend']
    )

    fig.update_traces(marker=dict(size=10, opacity=0.6))
    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)


def show_similar_patterns_table(similar_df, target_div):
    """Show table of similar historical patterns."""
    st.subheader(f"📊 Pattern Simili al Dividendo del {target_div}")

    if similar_df.empty:
        st.info("⚠️ Nessun pattern simile trovato con la soglia attuale")
        return

    # Select relevant columns
    display_cols = ['ex_date', 'similarity', 'dividend', 'gap_pct']

    # Add recovery metrics if available
    recovery_cols = ['recovery_d5_pct', 'recovery_d10_pct', 'gap_recovery_d5_pct', 'days_to_50pct_gap']
    for col in recovery_cols:
        if col in similar_df.columns:
            display_cols.append(col)

    display_df = similar_df[display_cols].copy()

    # Format columns
    display_df['similarity'] = display_df['similarity'].apply(lambda x: f"{x:.1%}")
    display_df['dividend'] = display_df['dividend'].apply(lambda x: f"€{x:.4f}")
    display_df['gap_pct'] = display_df['gap_pct'].apply(lambda x: f"{x:.2f}%")

    if 'recovery_d5_pct' in display_df.columns:
        display_df['recovery_d5_pct'] = display_df['recovery_d5_pct'].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )

    if 'gap_recovery_d5_pct' in display_df.columns:
        display_df['gap_recovery_d5_pct'] = display_df['gap_recovery_d5_pct'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )

    # Rename columns
    display_df = display_df.rename(columns={
        'ex_date': 'Ex-Date',
        'similarity': 'Similarità',
        'dividend': 'Dividendo',
        'gap_pct': 'Gap %',
        'recovery_d5_pct': 'Recovery D+5',
        'recovery_d10_pct': 'Recovery D+10',
        'gap_recovery_d5_pct': 'Gap Rec. D+5',
        'days_to_50pct_gap': 'Giorni a 50% Gap'
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Statistics
    st.markdown("### 📈 Statistiche Pattern Simili")
    col1, col2, col3 = st.columns(3)

    with col1:
        if 'Recovery D+5' in display_df.columns:
            # Extract numeric values
            recovery_vals = similar_df['recovery_d5_pct'].dropna()
            if len(recovery_vals) > 0:
                st.metric("Recovery D+5 Medio", f"{recovery_vals.mean():.2f}%")

    with col2:
        if 'Gap Rec. D+5' in display_df.columns:
            gap_rec_vals = similar_df['gap_recovery_d5_pct'].dropna()
            if len(gap_rec_vals) > 0:
                st.metric("Gap Recovery D+5 Medio", f"{gap_rec_vals.mean():.1f}%")

    with col3:
        if 'Giorni a 50% Gap' in display_df.columns:
            days_vals = similar_df['days_to_50pct_gap'].dropna()
            if len(days_vals) > 0:
                st.metric("Giorni Medi a 50% Gap", f"{days_vals.mean():.1f}")


# ============================================================================
# MAIN UI
# ============================================================================

st.title("🔍 Pattern Analysis - Pre-Dividendo → Post-Dividendo")

st.markdown("""
Questa analisi cerca **correlazioni** tra il comportamento del titolo **PRIMA** del dividendo
e il **recovery DOPO** il dividendo.

**Obiettivo**: Identificare segnali predittivi nel comportamento pre-dividendo che anticipano
il tipo di recovery post-dividendo.

**Come funziona**:
1. Estrae features da finestre temporali pre-dividendo (D-40 → D-1)
2. Calcola metriche di recovery post-dividendo (D0 → D+15)
3. Cerca correlazioni tra pre e post
4. Identifica pattern simili storici
""")

session = get_session()

# ============================================================================
# STOCK SELECTION
# ============================================================================

st.divider()
st.subheader("📊 Selezione Titolo")

stocks = session.query(Stock).all()
if not stocks:
    st.error("❌ Nessun titolo nel database")
    st.stop()

stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}
selected = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
stock = stock_options[selected]

# Get dividends
dividends = session.query(Dividend).filter_by(stock_id=stock.id).order_by(Dividend.ex_date).all()

if not dividends:
    st.warning(f"⚠️ Nessun dividendo per {stock.ticker}")
    st.stop()

if len(dividends) < cfg.pattern_analysis.min_patterns_for_analysis:
    st.warning(
        f"⚠️ Troppo pochi dividendi per analisi pattern: {len(dividends)} < {cfg.pattern_analysis.min_patterns_for_analysis}"
    )
    st.info("💡 Sono necessari almeno 3 dividendi storici per un'analisi significativa")
    st.stop()

st.success(f"✅ Trovati {len(dividends)} dividendi storici per {stock.ticker}")

# ============================================================================
# PATTERN ANALYSIS
# ============================================================================

if st.button("🚀 Avvia Analisi Pattern", type="primary"):
    with st.spinner("Analisi in corso... (può richiedere alcuni secondi)"):
        try:
            with OperationLogger(logger, "pattern_analysis", stock_ticker=stock.ticker):
                # Analyze all dividends
                patterns_df = analyze_all_dividends(session, stock.id, dividends)

            if patterns_df.empty:
                st.error("❌ Impossibile analizzare i dividendi (dati insufficienti)")
                st.stop()

            st.success(f"✅ Analizzati {len(patterns_df)} dividendi su {len(dividends)}")

            # Save to session state
            st.session_state['patterns_df'] = patterns_df
            st.session_state['stock'] = stock

        except Exception as e:
            st.error(f"❌ Errore durante l'analisi: {str(e)}")
            logger.error(f"Pattern analysis error: {e}", exc_info=True)
            import traceback
            st.code(traceback.format_exc())
            st.stop()

# ============================================================================
# RESULTS DISPLAY
# ============================================================================

if 'patterns_df' in st.session_state:
    patterns_df = st.session_state['patterns_df']
    stock = st.session_state['stock']

    st.divider()
    st.header("📊 Risultati Analisi")

    # Tab organization
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔗 Correlazioni",
        "📈 Scatter Plots",
        "🔍 Pattern Simili",
        "📋 Dataset Completo"
    ])

    # ========================================================================
    # TAB 1: CORRELATIONS
    # ========================================================================

    with tab1:
        st.subheader("🔗 Correlazioni Pre-Dividendo ← → Post-Dividendo")

        # Find correlations
        corr_df = find_correlations(patterns_df)

        if not corr_df.empty:
            st.markdown(f"**Trovate {len(corr_df)} correlazioni significative**")

            # Heatmap
            create_correlation_heatmap(corr_df)

            # Top correlations table
            st.markdown("### 📊 Top 10 Correlazioni")
            top_corr = corr_df.head(10).copy()
            top_corr['correlation'] = top_corr['correlation'].apply(lambda x: f"{x:.3f}")

            top_corr = top_corr.rename(columns={
                'pre_feature': 'Feature Pre-Dividendo',
                'post_metric': 'Metrica Post-Dividendo',
                'correlation': 'Correlazione'
            })

            st.dataframe(top_corr, use_container_width=True, hide_index=True)

        else:
            st.info("ℹ️ Nessuna correlazione significativa trovata con la soglia attuale")
            st.caption(f"Soglia minima: {cfg.pattern_analysis.min_correlation_threshold}")

    # ========================================================================
    # TAB 2: SCATTER PLOTS
    # ========================================================================

    with tab2:
        st.subheader("📈 Scatter Plot - Esplora Relazioni")

        if not corr_df.empty:
            # Let user select correlation to visualize
            top_pairs = corr_df.head(20)

            selected_corr = st.selectbox(
                "Seleziona correlazione da visualizzare",
                options=range(len(top_pairs)),
                format_func=lambda i: f"{top_pairs.iloc[i]['pre_feature']} ← → {top_pairs.iloc[i]['post_metric']} (r={top_pairs.iloc[i]['correlation']:.3f})"
            )

            pre_feat = top_pairs.iloc[selected_corr]['pre_feature']
            post_met = top_pairs.iloc[selected_corr]['post_metric']

            plot_scatter_correlation(patterns_df, pre_feat, post_met)

            # Statistical summary
            st.markdown("### 📊 Statistiche")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Feature Pre-Dividendo", pre_feat)
                if pre_feat in patterns_df.columns:
                    st.write(f"Media: {patterns_df[pre_feat].mean():.2f}")
                    st.write(f"Std Dev: {patterns_df[pre_feat].std():.2f}")

            with col2:
                st.metric("Metrica Post-Dividendo", post_met)
                if post_met in patterns_df.columns:
                    st.write(f"Media: {patterns_df[post_met].mean():.2f}")
                    st.write(f"Std Dev: {patterns_df[post_met].std():.2f}")

        else:
            st.info("Nessuna correlazione da visualizzare")

    # ========================================================================
    # TAB 3: SIMILAR PATTERNS
    # ========================================================================

    with tab3:
        st.subheader("🔍 Trova Pattern Simili")

        st.markdown("""
        Seleziona un dividendo storico e trova eventi simili in base al comportamento pre-dividendo.
        Utile per previsioni basate su analogie storiche.
        """)

        # Select target dividend
        div_options = {
            f"{row['ex_date']} - €{row['dividend']:.4f}": idx
            for idx, row in patterns_df.iterrows()
        }

        selected_div = st.selectbox("Seleziona Dividendo Target", list(div_options.keys()))
        target_idx = div_options[selected_div]

        # Similarity threshold
        similarity_threshold = st.slider(
            "Soglia Similarità",
            min_value=0.5,
            max_value=1.0,
            value=cfg.pattern_analysis.similarity_threshold,
            step=0.05,
            help="Similarità minima per pattern matching (cosine similarity)"
        )

        if st.button("🔍 Trova Pattern Simili"):
            with st.spinner("Ricerca pattern simili..."):
                similar_df = find_similar_patterns(
                    patterns_df,
                    target_idx,
                    similarity_threshold=similarity_threshold,
                    top_n=10
                )

                show_similar_patterns_table(similar_df, selected_div)

    # ========================================================================
    # TAB 4: FULL DATASET
    # ========================================================================

    with tab4:
        st.subheader("📋 Dataset Completo")

        st.markdown(f"""
        **Numero dividendi**: {len(patterns_df)}
        **Features totali**: {len(patterns_df.columns)}
        **Periodo**: {patterns_df['ex_date'].min()} → {patterns_df['ex_date'].max()}
        """)

        # Download button
        csv = patterns_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Scarica CSV",
            data=csv,
            file_name=f"{stock.ticker}_pattern_analysis.csv",
            mime="text/csv"
        )

        # Show dataframe
        st.dataframe(patterns_df, use_container_width=True, height=400)

        # Column info
        with st.expander("📊 Info Colonne"):
            st.markdown(f"**Totale colonne**: {len(patterns_df.columns)}")

            pre_cols = [c for c in patterns_df.columns if 'D-' in c or 'D_' in c]
            post_cols = [c for c in patterns_df.columns if 'recovery' in c or 'gap' in c]

            st.markdown(f"- **Features Pre-Dividendo**: {len(pre_cols)}")
            st.markdown(f"- **Metriche Post-Dividendo**: {len(post_cols)}")

            st.code("\n".join(patterns_df.columns.tolist()))

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("""
💡 **Come interpretare i risultati**:
- **Correlazioni positive forti (>0.5)**: Feature pre-dividendo è un buon predittore della metrica post
- **Correlazioni negative forti (<-0.5)**: Feature pre-dividendo è un contro-indicatore
- **Pattern Simili**: Eventi passati con comportamento pre-dividendo simile → recovery simile atteso
""")
