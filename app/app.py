
import streamlit as st
import plotly.express as px
import pandas as pd
import os
import random
import ssl
import time
import json
import threading
import requests

from datetime import datetime, timedelta
from collections import deque
from paho.mqtt.client import Client, MQTTv311, CallbackAPIVersion

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

# Configuración de MQTT
mqtt_broker = st.secrets["MQTT_BROKER"]
mqtt_port = int(st.secrets["MQTT_PORT"])
mqtt_user = st.secrets["MQTT_USER"]
mqtt_pass = st.secrets["MQTT_PASS"]
mqtt_topic = st.secrets["MQTT_TOPIC"]

# Clave del payload a mostrar
key = "p_total"
# Mapeo de dispositivos a zonas
device_map = { "zonaalta": "Zona Alta", 
               "zonamedia": "Zona Media",
               "zonabaja": "Zona Baja"}
# Definición de los límites para cada zona
device_thresholds = {"zonaalta": {"min": -2, "max": 2},
                     "zonamedia": {"min": -2, "max": 2},
                     "zonabaja": {"min": -1.5, "max": 1.5}}

device_names = device_map.keys()
# Inicializar datos en session_state
if "datos_mqtt" not in st.session_state:
    mqtt_data = {
        name: {
            "values": deque(maxlen=360),
            "last_ts": 0
        } for name in device_names
    }
    st.session_state["datos_mqtt"] = mqtt_data

mqtt_data = st.session_state["datos_mqtt"]

# Inicializar conexión MQTT
def iniciar_mqtt():
    if "mqtt_thread" not in st.session_state:
        def mqtt_loop():
            try:
                client_id = f"ibbi-energia-{random.randint(0, 10000)}"
                # print(client_id, mqtt_user, mqtt_pass, mqtt_broker, mqtt_port, mqtt_topic)
                # Crear cliente con versión moderna del API
                client = Client(
                    client_id=client_id,
                    clean_session=True,
                    protocol=MQTTv311,
                    callback_api_version=CallbackAPIVersion.VERSION2
                )
                client.on_connect = on_connect
                client.on_message = on_message
                client.on_disconnect = on_disconnect
                # Configurar credenciales
                client.username_pw_set(username=mqtt_user, password=mqtt_pass)
                # Configuración TLS (opcional)
                client.tls_set(cert_reqs=ssl.CERT_NONE)
                # Conectar al broker
                print("🟡 Conectando al broker MQTT...")
                client.connect(mqtt_broker, mqtt_port)
                time.sleep(1)  # Esperar unos segundos para asegurar la conexión
                client.subscribe(mqtt_topic)
                client.loop_forever()  # Iniciar el bucle de red en segundo plano
                # start_time = datetime.now()
                # max_duration = timedelta(minutes=1)

                # Ejecutar el bucle de red sin bloquear indefinidamente
                # while True:
                #     client.loop(timeout=1.0)  # Bucle no bloqueante
                #     elapsed = datetime.now() - start_time
                #     print(elapsed)
                #     if elapsed >= max_duration:
                #         print("⏱️ Tiempo máximo de conexión alcanzado (24h). Desconectando...")
                #         client.disconnect()
                #         st.session_state["mqtt_thread"] = None
                #         break
                #     time.sleep(1)
            except Exception as e:
                print(f"Error al conectar al broker MQTT: {e}")
                return
            
        t = threading.Thread(target=mqtt_loop, daemon=True)
        t.start()
        st.session_state["mqtt_thread"] = t

# Callback al conectar
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Conectado al broker MQTT")
    else:
        print(f"❌ Error al conectar. Código: {rc}")

def on_disconnect(client, userdata, flags, rc, properties=None):
    print("🔌 Desconectado del broker")

# Callback al recibir un mensaje
def on_message(client, userdata, msg):
    global mqtt_data
    device = msg.topic.split("/")[-1]
    if device in mqtt_data:
        try:
            payload = json.loads(msg.payload.decode())
            if key not in payload:
                print(f"⚠️ Clave '{key}' no encontrada en el mensaje de {device}. Payload: {payload}")
                return
            potencia = float(payload[key])
            mqtt_data[device]["values"].append({
                                                "ts": datetime.now(),
                                                "value": potencia
                                            })
            mqtt_data[device]["last_ts"] = time.time()
        except Exception as e:
            print(f"Error en lectura MQTT: {e}")

# Iniciar conexión MQTT
iniciar_mqtt()

# Configuración de la página
st.set_page_config(layout="wide")
st.title("iBBi - Monitor de Energía IES San Marcos")

now_ts = time.time()

# Combinar las tres series en un DataFrame largo
# Inicializamos una lista para todos los registros
registros = []

for dispositivo, datos in mqtt_data.items():
    for entrada in datos["values"]:
        registros.append({
            "ts": entrada["ts"],
            "valor": entrada["value"],
            "dispositivo": dispositivo
        })
# Si no hay al menos 6 registros, mostramos un mensaje y detenemos la ejecución
if len(registros) < 6:
    st.info("No hay datos disponibles aún.")
else:
    # Convertimos a DataFrame
    df_total = pd.DataFrame(registros)
    df_total["ts"] = pd.to_datetime(df_total["ts"])  # Asegura que es datetime
    df_total["ts"] = df_total["ts"].dt.floor("10s")  # Redondea a múltiplos de 15s
    df_total = df_total.sort_values(by=["ts", "dispositivo"]).reset_index(drop=True)

    # st.dataframe(df_total)
    fig = px.area(df_total, x="ts", y="valor", color="dispositivo",
                labels={"ts": "Hora", "valor": "Potencia (kW)"},
                title="Consumo energético por zona",
                color_discrete_sequence=px.colors.qualitative.Set2)
                
    fig.update_layout(xaxis=dict(tickformat="%H:%M:%S"))
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Últimos valores")
        total = 0
        for device_name in device_names:
            # Mostrar métricas generales
            df_device = df_total[df_total["dispositivo"] == device_name]    
            if not df_device.empty:
                st.metric(device_map[device_name], f"{df_device['valor'].iloc[-1]:.2f} kW")
                total += df_device['valor'].iloc[-1]
        st.metric("Total", f"{total:.2f} kW")
        
# Estado de conexión
# st.subheader("🌐 Conectividad")
col1, col2, col3 = st.columns(3)
for col, device_name in zip([col1, col2, col3], device_names):
    # st.markdown(f"### {device_name.capitalize()}")
    ts = mqtt_data[device_name]["last_ts"]
    last_dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    delta = now_ts - ts
    if delta < 15:
        estado = "🟢 ACTIVO"
    elif delta < 30:
        estado = "🟡 RETRASADO"
    else:
        estado = "🔴 DESCONECTADO"
    col.metric(label=device_map[device_name].upper(), value=estado, delta=f"{int(delta)} s")

# st.subheader("Detección de Anomalías")
col4, col5, col6 = st.columns(3)
for col, device_name in zip([col4, col5, col6], device_names):
    datos = list(mqtt_data[device_name]["values"])
    if datos:
        df = pd.DataFrame(datos)
        # Calcular media y límites
        media = df["value"].mean()
        thresholds = device_thresholds[device_name]
        min_threshold = media + media * thresholds["min"]
        max_threshold = media + media * thresholds["max"]
        
        if device_name == "zonaalta":
            max_threshold = min(max_threshold, 7.5)  # No puede superar 7.5 kW  # No puede ser mayor que 7.5kW
        elif device_name == "zonamedia":
            max_threshold = min(max_threshold, 5)  # No puede ser mayor que 5kW
            min_threshold = max(min_threshold, 0)  # No puede ser menor que 0 kW
        elif device_name == "zonabaja":
            min_threshold = max(min_threshold, 0)  # No puede ser menor que 0 kW
        # Añadir valores
        fig = px.line(df, x="ts", y="value", labels={"ts": "Hora", "value": "Potencia (kW)"}, title=f"{device_map[device_name]}")
        fig.update_layout(xaxis=dict(tickformat="%H:%M:%S"))
        annotation_text_min = f"{min_threshold:.2f} kW"
        annotation_text_max = f"{max_threshold:.2f} kW"
        # Añadir líneas de referencia
        fig.add_hline(y=media, line_dash="dot", line_color="red", annotation_text="Media", annotation_position="top left")
        fig.add_hline(y=min_threshold, line_dash="dash", line_color="orange", annotation_text=annotation_text_min, annotation_position="bottom left")
        fig.add_hline(y=max_threshold, line_dash="dash", line_color="orange", annotation_text=annotation_text_max, annotation_position="top left")

        col.plotly_chart(fig, use_container_width=True)

        # Comprobar si hay anomalías (siempre que haya al menos 10 valores registrados)
        if delta < 10 and df["value"].iloc[-1] < min_threshold or df["value"].iloc[-1] > max_threshold:
            st.toast(f"{last_dt} Anomalía detectada en {device_name}!", icon="🚨")
            print(f"🚨 Anomalía detectada en {device_name} ({last_dt})")
            # Aquí puedes añadir lógica para enviar alertas o notificaciones
    else:
        col.info("Sin datos disponibles aún.")

# Refresco automático
time.sleep(5)
st.rerun()