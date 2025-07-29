import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Análisis de Asignaturas IE", layout="wide")
st.title("📚 Análisis de Asignaturas desde Múltiples Excels")

uploaded_files = st.file_uploader("Carga uno o varios archivos Excel", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip().str.upper().str.replace(' ', '_')

            if 'SESIONES' not in df.columns:
                st.warning(f"⚠️ El archivo '{file.name}' no contiene una columna 'SESIONES'. Saltando...")
                continue

            df['SESSIONS'] = df['SESIONES'].astype(str).str.extract(r'(\d+)')[0]
            df['SESSIONS'] = pd.to_numeric(df['SESSIONS'], errors='coerce').fillna(0).astype(int)

            all_data.append(df)

        except Exception as e:
            st.error(f"❌ Error procesando el archivo {file.name}: {e}")

    if all_data:
        data = pd.concat(all_data, ignore_index=True)
        st.markdown(f"🔢 **Total de sesiones:** `{data['SESSIONS'].sum()}` — 📚 **Asignaciones cargadas:** `{data.shape[0]}`")

        tabs = st.tabs([
            "📌 Resumen general",
            "📊 Visualizaciones",
            "🗂️ Filtros combinados",
            "🕓 Línea temporal",
            "⬇️ Exportar",
            "📄 Datos detallados",
            "🔎 Filtro por columna"
        ])

        # TAB 1: RESUMEN GENERAL
        with tabs[0]:
            area_summary = data.groupby('AREA')['SESSIONS'].agg(['count', 'sum']).reset_index()
            area_summary.columns = ['Área', 'Nº de asignaturas', 'Total sesiones']
            tipo_summary = data.groupby('TIPO_ASIG.')['SESSIONS'].agg(['count', 'sum']).reset_index()
            tipo_summary.columns = ['Tipo de asignatura', 'Nº', 'Total sesiones']

            st.subheader("Resumen por Área")
            st.dataframe(area_summary)

            st.subheader("Resumen por Tipo de Asignatura")
            st.dataframe(tipo_summary)

        # TAB 2: VISUALIZACIONES
        with tabs[1]:
            col1, col2 = st.columns(2)
            with col1:
                fig_area = px.bar(area_summary, x='Área', y='Total sesiones', text='Total sesiones', title='Total de sesiones por Área')
                st.plotly_chart(fig_area, use_container_width=True)

            with col2:
                fig_tipo = px.pie(tipo_summary, names='Tipo de asignatura', values='Total sesiones', title='Distribución por Tipo')
                st.plotly_chart(fig_tipo, use_container_width=True)

            st.markdown("### Comparación por programa o año")
            field = st.selectbox("Selecciona una dimensión para comparar (eje X)", ['CURSO', 'PERIODO_ACADÉMICO', 'PROGRAMA'])
            facet = st.selectbox("¿Deseas dividir por otra variable?", ['TIPO_ASIG.', 'AREA', None])

            if field in data.columns:
                fig_comp = px.bar(data, x=field, y='SESSIONS', color=facet if facet else None,
                                  title="Sesiones por " + field, barmode="group", facet_col=facet if facet else None)
                st.plotly_chart(fig_comp, use_container_width=True)

        # TAB 3: FILTROS COMBINADOS
        with tabs[2]:
        st.markdown("### 🔎 Filtra por profesor + tipo de participación + programa")
    
        prof = st.multiselect("Profesor", options=data['PROFESOR'].dropna().unique())
        tipo_p = st.multiselect("Tipo P.", options=data['TIPO_P.'].dropna().unique())
        prog = st.multiselect("Programa", options=data['PROGRAMA'].dropna().unique())
    
        filtro = data.copy()
        if prof:
            filtro = filtro[filtro['PROFESOR'].isin(prof)]
        if tipo_p:
            filtro = filtro[filtro['TIPO_P.'].isin(tipo_p)]
        if prog:
            filtro = filtro[filtro['PROGRAMA'].isin(prog)]
    
        # Columnas que deseas mostrar en la tabla
        columnas_mostrar = ['PROFESOR', 'TIPO_P.', 'PROGRAMA', 'SECCIÓN', 'NOMBRE_DE_LA_ASIGNATURA', 'SESSIONS']
        columnas_presentes = [col for col in columnas_mostrar if col in filtro.columns]
    
        st.dataframe(filtro[columnas_presentes])
        st.markdown(f"🎯 **Total sesiones filtradas:** {filtro['SESSIONS'].sum()}")
        st.download_button("📥 Descargar resultados combinados", filtro[columnas_presentes].to_csv(index=False), file_name="filtro_combinado.csv")
    

        # TAB 4: LÍNEA TEMPORAL
        with tabs[3]:
            if 'FECHA_DESDE' in data.columns and 'FECHA_HASTA' in data.columns:
                df_timeline = data.copy()
                df_timeline['FECHA_DESDE'] = pd.to_datetime(df_timeline['FECHA_DESDE'], errors='coerce')
                df_timeline['FECHA_HASTA'] = pd.to_datetime(df_timeline['FECHA_HASTA'], errors='coerce')

                st.markdown("### 📆 Línea temporal por profesor")
                timeline_field = st.selectbox("Agrupar por", ['PROFESOR', 'AREA', 'CURSO'])

                fig_time = px.timeline(df_timeline.sort_values(by='FECHA_DESDE'),
                                       x_start="FECHA_DESDE", x_end="FECHA_HASTA",
                                       y=timeline_field, color='TIPO_ASIG.', title="Calendario de Asignaturas")
                fig_time.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.warning("No se detectaron columnas de fecha 'FECHA_DESDE' y 'FECHA_HASTA'.")

        # TAB 5: EXPORTAR
        with tabs[4]:
            st.markdown("### 📁 Exportar resúmenes a CSV")
            st.download_button("📥 Descargar resumen por área", area_summary.to_csv(index=False), file_name="resumen_area.csv")
            st.download_button("📥 Descargar resumen por tipo", tipo_summary.to_csv(index=False), file_name="resumen_tipo.csv")

        # TAB 6: DATOS DETALLADOS
        with tabs[5]:
            st.markdown("### 📋 Tabla detallada con columnas completas")

            full_columns = [
                'ID', 'NOMBRE_DE_LA_ASIGNATURA', 'ASIGNATURA_OFICIAL_EQUIVALENTE', 'CRÉDITOS_OFICIALES', 'PROGRAMA',
                'CONVOCATORIA', 'SECCIÓN', 'CAMPUS', 'CURSO', 'CÓD._PROFESOR', 'PROFESOR', 'EMAIL_FACULTY',
                'TIPO_PRO.', 'DOCTORADO', 'ACREDITACIÓN', 'FECHA_DESDE', 'FECHA_HASTA', 'PERIODO_DE_IMPARTICIÓN',
                'PERIODO_ACADÉMICO', 'SESIONES', 'S._LV-IP', 'S._ASYNC', 'FORO', 'S._TUTOR', 'S._LV-OL',
                'IDIOMA', 'AREA', 'TIPO_ASIG.', 'TIPO_P.', 'OBS._DIR_ÁREA', 'OBS._DIR_PROG.',
                'PAGO_ESTÁNDAR', 'OK_DP', 'RES._ASIG.'
            ]

            available_cols = [col for col in full_columns if col in data.columns]
            df_detalle = data[available_cols].copy()
            df_detalle['Total'] = data['SESSIONS']

            st.dataframe(df_detalle)
            st.download_button("📥 Descargar tabla completa (CSV)", df_detalle.to_csv(index=False), file_name="asignaturas_detalladas.csv")

        # TAB 7: FILTRO POR COLUMNA
        with tabs[6]:
            st.markdown("### 🔍 Filtro dinámico por cualquier columna")

            filterable_cols = [col for col in data.columns if data[col].nunique() < 50 and data[col].dtype == object]

            selected_col = st.selectbox("Selecciona una columna para filtrar", filterable_cols)

            if selected_col:
                opciones = data[selected_col].dropna().unique().tolist()
                selected_vals = st.multiselect("Selecciona valores", opciones, default=opciones)

                df_filtered = data[data[selected_col].isin(selected_vals)]

                st.dataframe(df_filtered)
                st.markdown(f"🔢 **Total filas filtradas:** {df_filtered.shape[0]} — **Total sesiones:** {df_filtered['SESSIONS'].sum()}")

                st.download_button("📥 Descargar resultados filtrados", df_filtered.to_csv(index=False), file_name="filtro_columna.csv")
