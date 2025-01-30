import streamlit as st 
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
import plotly.express as px
import datetime
import watchdog

st.set_page_config(layout="wide")

def color_puntuacion_seguridad(val):
    try:
        # Convertir el valor a float
        num_val = float(val)
        if pd.isna(num_val):
            return ''
        elif num_val >= 90:
            return 'background-color: #92d050'  # verde claro
        elif num_val >= 70:
            return 'background-color: #ffff00'  # amarillo
        else:
            return 'background-color: #FF0000'  # rojo claro
    except (ValueError, TypeError):
        return ''

def cargar_informe_unidades():
    return pd.read_excel('data/Informe_Diario_Unidades.xlsx', index_col=None)

def cargar_informe_mensual_unidades():
    return pd.read_excel('data/Informe_Mensual_Unidades.xlsx', index_col=None)

def cargar_paradas_unidades():
    hojas = pd.read_excel('data/PARADAS_UNIDADES.xlsx', sheet_name=None, index_col=None)
    for key in hojas:
        hojas[key] = hojas[key].reset_index(drop=True)
    return hojas

def cargar_paradas_unidades_coord():
    return pd.read_excel('data/PARADAS_UNIDADES_COORD.xlsx', index_col=None)

def cargar_incidentes_diarios():
    return pd.read_excel('data/eventos_diario.xlsx', index_col=None)

# Cargar los datos
df_paradas = cargar_paradas_unidades()
df_paradas_coord = cargar_paradas_unidades_coord()
df_incidentes = cargar_incidentes_diarios().reset_index(drop=True)

# Página principal
st.title("Página Principal - Integración Reparto PFR")

# Selección inicial de unidad
unidad_seleccionada = st.selectbox(
    "Selecciona una unidad",
    options=["Todas"] + list(cargar_informe_unidades()['Número de unidad'].unique()),
    key="unidad_selector"
)

# Mostrar datos según la unidad seleccionada
if unidad_seleccionada == "Todas":
    st.subheader("Información Seguridad de Unidades")
    modo_informe = st.radio(
        "Selecciona el tipo de informe de seguridad:",
        ("Informe Diario", "Informe Mensual"),
        key="modo_informe"
    )
    
    if modo_informe == "Informe Diario":
        df_unidades = cargar_informe_unidades().reset_index(drop=True)
    else:
        df_unidades = cargar_informe_mensual_unidades().reset_index(drop=True)

    # Convertir la columna 'Puntuación de seguridad' a numérica
    df_unidades['Puntuación de seguridad'] = pd.to_numeric(df_unidades['Puntuación de seguridad'], errors='coerce').round().astype('Int64')
    columnas_predeterminadas = ['Número de unidad', 'Operador', 'Modelo', 'Distancia total km', 'Combustible consumido (L)', 'Puntuación de seguridad']
    columnas_disponibles = list(df_unidades.columns.difference(columnas_predeterminadas))

    columnas_seleccionadas = st.multiselect(
        "Selecciona las columnas adicionales para mostrar",
        options=columnas_disponibles,
        default=[]
    )

    columnas_finales = columnas_predeterminadas + columnas_seleccionadas

    # Aplicar el estilo condicional a la tabla
    df_styled = df_unidades[columnas_finales].style.applymap(
        color_puntuacion_seguridad,
        subset=['Puntuación de seguridad']
    )

    st.write("Informe de Unidades", df_styled)

    st.subheader("Gráfico de Correlación - Distancia y Combustible")
    fig = px.scatter(
        df_unidades,
        x='Distancia total km',
        y='Combustible consumido (L)',
        hover_data={'Número de unidad': True, 'Operador': True},
        labels={"Distancia total km": "Distancia (km)", "Combustible consumido (L)": "Combustible (L)"},
        title="Relación entre Distancia y Combustible Consumido"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Mostrar estadísticas generales", expanded=False):
        df_unidades['Combustible consumido (L)'] = pd.to_numeric(df_unidades['Combustible consumido (L)'], errors='coerce')
        total_litros = df_unidades['Combustible consumido (L)'].sum()
        df_unidades['Distancia total km'] = pd.to_numeric(df_unidades['Distancia total km'], errors='coerce')
        total_kilometros = df_unidades['Distancia total km'].sum()
        promedio_litros_unidad = total_litros / df_unidades.shape[0]
        promedio_km_unidad = total_kilometros / df_unidades.shape[0]

        st.metric("Total Litros Consumidos", f"{total_litros:.2f} L")
        st.metric("Total Kilómetros Recorridos", f"{total_kilometros:.2f} km")
        st.metric("Promedio Litros por Unidad", f"{promedio_litros_unidad:.2f} L/unidad")
        st.metric("Promedio Kilómetros por Unidad", f"{promedio_km_unidad:.2f} km/unidad")


else:
    st.subheader("Informe de la Unidad")
    modo_informe = st.radio(
        "Selecciona el tipo de informe de seguridad:",
        ("Informe Diario", "Informe Mensual"),
        key="modo_informe"
    )

    if modo_informe == "Informe Diario":
        df_unidades = cargar_informe_unidades().reset_index(drop=True)
    else:
        df_unidades = cargar_informe_mensual_unidades().reset_index(drop=True)

    unidad_info = df_unidades[df_unidades['Número de unidad'] == unidad_seleccionada]
    
    # Convertir la columna 'Puntuación de seguridad' a numérica
    unidad_info['Puntuación de seguridad'] = pd.to_numeric(unidad_info['Puntuación de seguridad'], errors='coerce').round().astype('Int64')
    
    columnas_predeterminadas = ['Número de unidad', 'Operador', 'Modelo', 'Distancia total km', 'Combustible consumido (L)', 'Puntuación de seguridad']
    columnas_disponibles = list(unidad_info.columns.difference(columnas_predeterminadas))

    columnas_seleccionadas = st.multiselect(
        "Selecciona las columnas adicionales para mostrar",
        options=columnas_disponibles,
        default=[],
        key="columnas_unidad"
    )

    columnas_finales = columnas_predeterminadas + columnas_seleccionadas
    
    # Aplicar el estilo condicional a la tabla de unidad específica
    unidad_info_styled = unidad_info[columnas_finales].style.applymap(
        color_puntuacion_seguridad,
        subset=['Puntuación de seguridad']
    )
    
    st.write(unidad_info_styled)

    # Selector para elegir entre eventos mensuales o diarios
    st.markdown("### **Eventos de seguridad:**")

    # Mostrar el radio button
    tipo_eventos = st.radio(
        "Selecciona el tipo de evento",  # Etiqueta del radio
        ("Día Anterior", "Acumulado Mensual"),
        key="tipo_eventos"
    )
    # Cargar el DataFrame correspondiente al tipo de eventos seleccionado
    if tipo_eventos == "Día Anterior":
        df_eventos = cargar_incidentes_diarios().reset_index(drop=True)
    else:
        df_eventos = pd.read_excel('data/eventos_mensual.xlsx', index_col=None).reset_index(drop=True)

    # Filtrar los incidentes para la unidad seleccionada
    incidentes_info = df_eventos[df_eventos['Unidad'] == unidad_seleccionada]

    # Verificar si hay incidentes para la unidad seleccionada
    if not incidentes_info.empty:
        # Filtrar solo las columnas necesarias para mostrar en la tabla
        columnas_mostrar = ['Tipo de evento', 'Operador', 'Hora', 'Unidad']
        st.write(f"{tipo_eventos} de la Unidad {unidad_seleccionada}", incidentes_info[columnas_mostrar].reset_index(drop=True))

        # Mostrar los videos correspondientes utilizando las columnas originales
        for _, row in incidentes_info.iterrows():
            st.subheader(f"Incidente: {row['Tipo de evento']} ----- Hora: {row['Hora']}")

            # Video Interior
            if pd.notna(row['video_Interior']) and row['video_Interior'] != "No video URL":
                st.write("**Video Interior**")
                video_url_interior = row['video_Interior']
                st.markdown(f'<video width="640" height="360" controls><source src="{video_url_interior}" type="video/mp4"></video>', unsafe_allow_html=True)
            else:
                st.write("**No hay video interior disponible.**")

            # Video Exterior
            if pd.notna(row['video_Exterior']) and row['video_Exterior'] != "No video URL":
                st.write("**Video Exterior**")
                video_url_exterior = row['video_Exterior']
                st.markdown(f'<video width="640" height="360" controls><source src="{video_url_exterior}" type="video/mp4"></video>', unsafe_allow_html=True)
            else:
                st.write("**No hay video exterior disponible.**")

    else:
        st.write(f"No se encontraron incidentes para la Unidad {unidad_seleccionada}.")

    # Mostrar paradas de la unidad seleccionada con el estilo aplicado
    if str(unidad_seleccionada) in df_paradas:
        paradas_info = df_paradas[str(unidad_seleccionada)].reset_index(drop=True)
        
        # Convertir la columna 'tiempo_espera' a timedelta si no lo es
        paradas_info['tiempo_espera'] = pd.to_timedelta(paradas_info['tiempo_espera'], errors='coerce')
        
        # Formatear la columna 'tiempo_espera' para mostrar solo horas, minutos y segundos
        paradas_info['tiempo_espera'] = paradas_info['tiempo_espera'].apply(lambda x: str(x).split()[2] if pd.notna(x) else '00:00:00')
        
        # Aplicar el estilo solo a las filas con 'tiempo_espera' mayor a 20 minutos
        paradas_info_styled = paradas_info.style.applymap(
            lambda val: 'background-color: red' if isinstance(val, str) and pd.to_timedelta(val) > pd.Timedelta(minutes=20) else '',
            subset=['tiempo_espera']
        )
        st.markdown(f"### **Paradas de la Unidad {unidad_seleccionada}:**")
        st.write(paradas_info_styled)
    else:
        st.write(f"No se encontraron paradas para la Unidad {unidad_seleccionada}.")

    st.subheader("Mapa de Paradas")

    paradas_coord_filtradas = df_paradas_coord[df_paradas_coord['unidad'] == int(unidad_seleccionada)]

    if not paradas_coord_filtradas.empty:
        centro = [
            paradas_coord_filtradas.iloc[0]['LATITUD'],
            paradas_coord_filtradas.iloc[0]['LONGITUD']
        ]
        mapa = folium.Map(location=centro, zoom_start=12)

        colores = {
            'NO ENTREGADO': 'orange',
            'ENTREGADO': 'green',
            'PARADA INVÁLIDA': 'red'
        }
        for _, row in paradas_coord_filtradas.iterrows():
            popup_info = f"""
                <strong>Nombre del Cliente:</strong> {row['NOMBRE_CLIENTE']}<br>
                <strong>Hora:</strong> {row['hora_final']}<br>
                <strong>Tiempo de Espera:</strong> {row['tiempo_espera']}<br>
                <strong>Estatus:</strong> {row['parada_status']}
            """
            folium.Marker(
                location=[row['LATITUD'], row['LONGITUD']],
                popup=popup_info,
                icon=folium.Icon(color=colores.get(row['parada_status'], 'blue'))
            ).add_to(mapa)

        st_folium(mapa, width=1600, height=600)
    else:
        st.write(f"No se encontraron coordenadas para la Unidad {unidad_seleccionada}.")