# 🔋 Monitorización en Tiempo Real de Consumo Energético con Streamlit y MQTT

Este proyecto forma parte del curso **"Ciencia de Datos e IA Aplicada para la Concienciación del Uso de Recursos"**, impartido al profesorado de Formación Profesional en el marco del proyecto iBBi.

El objetivo es desarrollar una aplicación web interactiva que permita monitorizar en tiempo real el consumo energético de distintas zonas de un centro educativo, utilizando herramientas accesibles como **Streamlit**, **Plotly** y el protocolo **MQTT**.

## 📌 Funcionalidades principales

- **Lectura en tiempo real de datos MQTT** simulados o desde dispositivos reales.
- **Visualización gráfica** de la potencia consumida por zona (`Zona Alta`, `Zona Media`, `Zona Baja`).
- **Indicador de conectividad** por dispositivo.
- **Detección de anomalías** en tiempo real basada en umbrales dinámicos.
- **Estadísticas básicas** (media, mínimo y máximo) de los últimos valores.
- **Historial de datos** y comparativas diarias.

## 🛠️ Tecnologías utilizadas

- [Streamlit](https://streamlit.io/) – Para la interfaz web
- [Plotly](https://plotly.com/python/) – Para los gráficos interactivos
- [paho-mqtt](https://www.eclipse.org/paho/) – Cliente MQTT en Python
- Python 3.10+

## 📂 Estructura del repositorio

```

├── app/
│   ├── app.py                  # Aplicación principal en Streamlit
│   └── config.yaml             # Configuración de tópicos y dispositivos
├── data/
│   └── example.csv             # Datos simulados para pruebas
├── requirements.txt
└── README.md

````

## 🚀 Instalación y ejecución

1. **Clona el repositorio:**

```bash
git clone https://github.com/CIFPSanMarcos/ibbi-monitor.git
cd ibbi-monitor
````

2. **Crea un entorno virtual e instala dependencias:**

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Ejecuta la aplicación:**

```bash
streamlit run app/app.py
```

> Por defecto, se inicia en modo de simulación de datos. Puedes activar el modo de producción con dispositivos MQTT reales en el archivo `config.yaml`.

## 🧠 Enfoque educativo

Este proyecto ha sido diseñado como un **ejercicio práctico para introducir conceptos de IoT, análisis en tiempo real y visualización de datos en el aula**, promoviendo el uso eficiente y sostenible de la energía.

## 📄 Licencia

MIT © 2025 - Proyecto iBBi