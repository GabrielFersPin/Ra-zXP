import streamlit as st
import pandas as pd
import datetime
import os

# Archivo donde se guardan las tareas
DATA_FILE = "task_log.csv"

# Inicializar archivo si no existe
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Fecha", "Categoría", "Tarea", "Puntos", "Comentario"])
    df_init.to_csv(DATA_FILE, index=False)

# Cargar datos existentes
df = pd.read_csv(DATA_FILE)

st.title("🎯 Personal Gamification Tracker")
st.sidebar.header("Agregar nueva tarea")

# Formulario para agregar tarea
with st.sidebar.form(key="new_task_form"):
    fecha = st.date_input("Fecha", datetime.date.today())
    categoria = st.selectbox("Categoría", ["Profesional", "Personal"])
    tarea = st.text_input("Tarea realizada")
    puntos = st.number_input("Puntos", min_value=1, max_value=100, step=1)
    comentario = st.text_area("Comentario (opcional)")
    submit_button = st.form_submit_button(label="Registrar tarea")

# Agregar tarea al archivo
if submit_button:
    new_row = pd.DataFrame([[fecha, categoria, tarea, puntos, comentario]],
                           columns=["Fecha", "Categoría", "Tarea", "Puntos", "Comentario"])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("✅ Tarea registrada exitosamente. ¡Sigue así!")

# Mostrar puntos acumulados
st.header("📈 Progreso actual")
total_puntos = df["Puntos"].sum()
st.metric("Puntos acumulados", total_puntos)

# Visualización de tareas
st.subheader("🗂️ Historial de tareas")
st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
