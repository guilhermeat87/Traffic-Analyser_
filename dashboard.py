import streamlit as st
import pandas as pd
import os
import tempfile
import shutil

st.set_page_config(layout="wide")
st.title("Dashboard de Análise de Simulação de Tráfego")
st.write("Faça o upload de um ou mais arquivos de relatório (.xls) para visualizar os resultados consolidados.")

# ==========================================================
# FUNÇÃO DE PROCESSAMENTO (TUDO JUNTO NO MESMO ARQUIVO)
# ==========================================================
def process_traffic_data(file_path):
    df = pd.read_excel(file_path)

    results = []
    current_section = None
    current_direction = None

    for _, row in df.iterrows():
        val0 = str(row[0]).strip()

        # Detectar seção
        if val0 in ['NWB', 'SEB', 'EB', 'WB']:
            current_section = val0
            continue

        # Detectar direção
        if 'Sentido' in val0:
            current_direction = val0
            continue

        # Detectar intervalo de tempo
        if ':' in val0 and len(val0.split(':')) == 3:
            try:
                results.append({
                    'Secao': current_section,
                    'Direcao': current_direction,
                    'Intervalo': val0,
                    'Atraso_Total_min': row[1],
                    'Atraso_Medio_seg_veic': row[2],
                    'Tempo_Parada_min': row[3],
                    'Tempo_Parada_Medio_seg_veic': row[4],
                    'Num_Paradas': row[5],
                    'Media_Paradas_veic': row[6]
                })
            except:
                pass

        # Detectar Summary
        if val0 == 'Summary':
            try:
                results.append({
                    'Secao': current_section,
                    'Direcao': current_direction,
                    'Intervalo': 'Summary',
                    'Atraso_Total_min': row[1],
                    'Atraso_Medio_seg_veic': row[2],
                    'Tempo_Parada_min': row[3],
                    'Tempo_Parada_Medio_seg_veic': row[4],
                    'Num_Paradas': row[[5]],
                    'Media_Paradas_veic': row[6]
                })
            except:
                pass

    return pd.DataFrame(results)


def run_processing(directory_path):
    all_results = []

    for file in os.listdir(directory_path):
        if file.endswith(".xls") or file.endswith(".xlsx"):
            file_path = os.path.join(directory_path, file)
            df_result = process_traffic_data(file_path)

            if not df_result.empty:
                df_result["Arquivo"] = file
                all_results.append(df_result)

    if all_results:
        return pd.concat(all_results, ignore_index=True)

    return pd.DataFrame()


# ==========================================================
# STREAMLIT - UPLOAD
# ==========================================================
uploaded_files = st.file_uploader(
    "Escolha os arquivos .xls",
    accept_multiple_files=True,
    type=['xls', 'xlsx']
)

if uploaded_files:
    temp_dir = tempfile.mkdtemp()

    for uploaded_file in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    results_df = run_processing(temp_dir)

    if results_df is not None and not results_df.empty:
        st.success(f"{len(uploaded_files)} arquivo(s) processado(s) com sucesso!")

        summary_df = results_df[results_df['Intervalo'] == 'Summary'].copy()

        if not summary_df.empty:
            st.header("Resultados do Sumário")

            summary_df.rename(columns={
                'Secao': 'Seção',
                'Direcao': 'Direção',
                'Atraso_Total_min': 'Atraso Total (min)',
                'Atraso_Medio_seg_veic': 'Atraso Médio (s/veic)',
                'Tempo_Parada_min': 'Tempo de Parada (min)',
                'Tempo_Parada_Medio_seg_veic': 'Tempo de Parada Médio (s/veic)',
                'Num_Paradas': 'Nº de Paradas',
                'Media_Paradas_veic': 'Média de Paradas/veic',
                'Arquivo': 'Arquivo'
            }, inplace=True)

            st.dataframe(summary_df)

            st.header("Visualização Gráfica do Sumário")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Atraso Médio por Direção")
                st.bar_chart(summary_df, x='Direção', y='Atraso Médio (s/veic)')

            with col2:
                st.subheader("Número de Paradas por Direção")
                st.bar_chart(summary_df, x='Direção', y='Nº de Paradas')

            col3, col4 = st.columns(2)

            with col3:
                st.subheader("Atraso Total (min) por Direção")
                st.bar_chart(summary_df, x='Direção', y='Atraso Total (min)')

            with col4:
                st.subheader("Tempo de Parada Total (min) por Direção")
                st.bar_chart(summary_df, x='Direção', y='Tempo de Parada (min)')

        else:
            st.warning("Nenhuma linha de 'Summary' foi encontrada nos arquivos processados.")

        if st.checkbox("Mostrar todos os dados (incluindo intervalos)"):
            st.header("Dados Completos")
            st.dataframe(results_df)

    else:
        st.error("Não foi possível processar os arquivos. Verifique o formato e o conteúdo.")

    shutil.rmtree(temp_dir, ignore_errors=True)

else:
    st.info("Aguardando o upload dos arquivos...")
