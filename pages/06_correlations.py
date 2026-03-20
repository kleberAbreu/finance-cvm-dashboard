"""
Página 6: Correlations - Análise de Correlações entre Métricas.
"""
import streamlit as st
import pandas as pd
from src.data.loader import load_and_prepare_base
from src.data.preprocessor import get_latest_quarter_data
from src.components.sidebar import render_sidebar_filters, apply_filters, render_export_buttons
from src.components.charts import create_scatter_matrix, create_heatmap
from src.utils.calculations import calculate_regression_stats
from config.settings import PARQUET_BASE_FILE

st.set_page_config(page_title="Correlations - Dashboard CVM", page_icon="🔗", layout="wide")

st.title("🔗 Análise de Correlações")

# Aplicar filtros
filters = render_sidebar_filters()

try:
    # Carregar dados
    df_base = load_and_prepare_base(PARQUET_BASE_FILE)
    df_filtered = apply_filters(df_base, filters)

    if len(df_filtered) == 0:
        st.warning("Nenhum dado disponível com os filtros aplicados")
        st.stop()

    # Usar dados mais recentes
    df_latest = get_latest_quarter_data(df_filtered)

    # Métricas disponíveis para análise
    available_metrics = [
        'Market Cap', 'EBITDA', 'Lucro Líquido',
        'P/E', 'EV/EBITDA', 'P/B', 'DL/EV',
        'Patrimônio Líquido', 'Dívida Líquida', 'Ativo Total'
    ]

    # Seleção de métricas para scatter plot
    st.header("📊 Scatter Plot com Regressão")

    col1, col2, col3 = st.columns(3)

    with col1:
        x_metric = st.selectbox(
            "Eixo X:",
            options=available_metrics,
            index=0,
            key='corr_x'
        )

    with col2:
        y_metric = st.selectbox(
            "Eixo Y:",
            options=available_metrics,
            index=4,
            key='corr_y'
        )

    with col3:
        color_by = st.selectbox(
            "Colorir por:",
            options=['Tipo', 'Nenhum'],
            key='corr_color'
        )

    # Opções adicionais
    col1, col2 = st.columns(2)

    with col1:
        size_by = st.selectbox(
            "Tamanho das bolhas:",
            options=['Nenhum', 'Market Cap', 'EBITDA', 'Ativo Total'],
            key='corr_size'
        )

    with col2:
        remove_outliers = st.checkbox(
            "Remover outliers (IQR)",
            value=False,
            key='corr_remove_outliers'
        )

    # Preparar dados
    df_plot = df_latest[[x_metric, y_metric]].copy()

    if color_by != 'Nenhum':
        df_plot[color_by] = df_latest[color_by]
    else:
        df_plot['Tipo'] = 'Todas'

    if size_by != 'Nenhum':
        df_plot[size_by] = df_latest[size_by]

    # Remover outliers se solicitado
    if remove_outliers:
        from src.data.preprocessor import remove_outliers as remove_outliers_func

        df_plot = remove_outliers_func(df_plot, x_metric, method='iqr', threshold=1.5)
        df_plot = remove_outliers_func(df_plot, y_metric, method='iqr', threshold=1.5)

    # Criar scatter plot
    fig_scatter = create_scatter_matrix(
        df_plot,
        x=x_metric,
        y=y_metric,
        color_by=color_by if color_by != 'Nenhum' else 'Tipo',
        size_by=size_by if size_by != 'Nenhum' else None,
        title=f"{y_metric} vs {x_metric}"
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

    # Estatísticas de regressão
    st.subheader("📈 Estatísticas de Regressão")

    stats = calculate_regression_stats(df_plot[x_metric], df_plot[y_metric])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Coeficiente (R)",
            f"{stats['r_value']:.4f}" if pd.notna(stats['r_value']) else "N/A"
        )

    with col2:
        st.metric(
            "R² (R-Squared)",
            f"{stats['r_squared']:.4f}" if pd.notna(stats['r_squared']) else "N/A"
        )

    with col3:
        st.metric(
            "P-Value",
            f"{stats['p_value']:.4e}" if pd.notna(stats['p_value']) else "N/A"
        )

    with col4:
        st.metric(
            "Slope",
            f"{stats['slope']:.4f}" if pd.notna(stats['slope']) else "N/A"
        )

    # Interpretação
    if pd.notna(stats['r_squared']):
        r_squared = stats['r_squared']
        p_value = stats['p_value']

        interpretation = []

        if r_squared > 0.7:
            interpretation.append("✅ **Correlação forte** (R² > 0.7)")
        elif r_squared > 0.4:
            interpretation.append("⚠️ **Correlação moderada** (0.4 < R² < 0.7)")
        else:
            interpretation.append("❌ **Correlação fraca** (R² < 0.4)")

        if p_value < 0.01:
            interpretation.append("✅ **Estatisticamente significativo** (p < 0.01)")
        elif p_value < 0.05:
            interpretation.append("⚠️ **Marginalmente significativo** (p < 0.05)")
        else:
            interpretation.append("❌ **Não significativo** (p ≥ 0.05)")

        st.info(" | ".join(interpretation))

    st.divider()

    # Matriz de correlação
    st.header("🔥 Matriz de Correlação")

    selected_metrics_matrix = st.multiselect(
        "Selecione métricas para matriz (até 10):",
        options=available_metrics,
        default=available_metrics[:6],
        max_selections=10,
        key='corr_matrix_metrics'
    )

    if len(selected_metrics_matrix) >= 2:
        fig_heatmap = create_heatmap(
            df_latest,
            metrics=selected_metrics_matrix,
            title="Matriz de Correlação"
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Tabela de correlações
        st.subheader("📋 Tabela de Correlações")

        from src.utils.calculations import calculate_correlation_matrix

        corr_matrix = calculate_correlation_matrix(df_latest, selected_metrics_matrix)

        st.dataframe(
            corr_matrix.style.background_gradient(cmap='RdBu', vmin=-1, vmax=1),
            use_container_width=True
        )

    st.divider()

    # Análise separada por setor
    st.header("🏭 Análise por Setor")

    analyze_by_sector = st.checkbox(
        "Analisar correlações separadamente por setor",
        value=False,
        key='corr_by_sector'
    )

    if analyze_by_sector:
        sectors = df_latest['Tipo'].unique().tolist()

        selected_sector = st.selectbox(
            "Selecione setor:",
            options=sectors,
            key='corr_sector'
        )

        df_sector = df_latest[df_latest['Tipo'] == selected_sector]

        st.subheader(f"Setor: {selected_sector}")

        # Scatter plot do setor
        fig_sector = create_scatter_matrix(
            df_sector,
            x=x_metric,
            y=y_metric,
            color_by='Tipo',
            size_by=size_by if size_by != 'Nenhum' else None,
            title=f"{y_metric} vs {x_metric} - {selected_sector}"
        )

        st.plotly_chart(fig_sector, use_container_width=True)

        # Estatísticas do setor
        stats_sector = calculate_regression_stats(df_sector[x_metric], df_sector[y_metric])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("R (Setor)", f"{stats_sector['r_value']:.4f}" if pd.notna(stats_sector['r_value']) else "N/A")

        with col2:
            st.metric("R² (Setor)", f"{stats_sector['r_squared']:.4f}" if pd.notna(stats_sector['r_squared']) else "N/A")

        with col3:
            st.metric("P-Value (Setor)", f"{stats_sector['p_value']:.4e}" if pd.notna(stats_sector['p_value']) else "N/A")

        with col4:
            n_companies = len(df_sector)
            st.metric("# Empresas", n_companies)

    st.divider()

    # Correlações ao longo do tempo
    st.header("⏱️ Correlações ao Longo do Tempo")

    st.info("Feature em desenvolvimento: Análise de como as correlações entre métricas evoluem trimestralmente")

    # Placeholder para análise temporal
    time_metrics = st.multiselect(
        "Selecione 2 métricas para análise temporal:",
        options=available_metrics,
        default=available_metrics[:2],
        max_selections=2,
        key='corr_time_metrics'
    )

    if len(time_metrics) == 2:
        st.write(f"Análise da correlação entre **{time_metrics[0]}** e **{time_metrics[1]}** ao longo do tempo")

        # Calcular correlação por trimestre
        correlations_over_time = []

        for date in df_filtered['Data_Trimestre'].unique():
            df_date = df_filtered[df_filtered['Data_Trimestre'] == date]

            if len(df_date) > 5:  # Mínimo de empresas
                corr = df_date[time_metrics].corr().iloc[0, 1]

                correlations_over_time.append({
                    'Data_Trimestre': date,
                    'Correlação': corr
                })

        if correlations_over_time:
            df_corr_time = pd.DataFrame(correlations_over_time)

            import plotly.graph_objects as go

            fig_time = go.Figure()

            fig_time.add_trace(go.Scatter(
                x=df_corr_time['Data_Trimestre'],
                y=df_corr_time['Correlação'],
                mode='lines+markers',
                name='Correlação',
                line=dict(color='steelblue', width=3)
            ))

            fig_time.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)

            fig_time.update_layout(
                title=f"Evolução da Correlação: {time_metrics[0]} vs {time_metrics[1]}",
                xaxis_title="Data",
                yaxis_title="Correlação",
                template='plotly_white',
                hovermode='x unified',
                font=dict(family="Inter", size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=50, b=10),
                hoverlabel=dict(bgcolor="#262730", font_size=13, font_family="Inter")
            )

            st.plotly_chart(fig_time, use_container_width=True)

    # Renderizar botões de exportação
    render_export_buttons(df_filtered)

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(traceback.format_exc())
