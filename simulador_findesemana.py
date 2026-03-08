import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os

def app():
    st.markdown("""
    <style>
    .metric-card { background-color: white; border-radius: 8px; padding: 10px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #004d40; }
    .pregunta-box { background-color: #e8f5e9; padding: 15px; border-left: 5px solid #2e7d32; border-radius: 5px; margin-bottom: 15px;}
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # VARIABLES DE ESTADO GLOBALES
    # ==========================================
    if 'fase' not in st.session_state: st.session_state.fase = 0
    if 'inicio_real' not in st.session_state: st.session_state.inicio_real = None
    if 'ultima_actualizacion' not in st.session_state: st.session_state.ultima_actualizacion = None

    if 'datos_planta' not in st.session_state: st.session_state.datos_planta = {}
    if 'estado_plc' not in st.session_state: st.session_state.estado_plc = "🟢 RUN"
    if 'utilidad_cop' not in st.session_state: st.session_state.utilidad_cop = 0 
    if 'aceite_lts' not in st.session_state: st.session_state.aceite_lts = 20000.0
    if 'metanol_lts' not in st.session_state: st.session_state.metanol_lts = 5000.0
    if 'biodiesel_prod' not in st.session_state: st.session_state.biodiesel_prod = 0.0
    if 'duracion_simulacion' not in st.session_state: st.session_state.duracion_simulacion = 600 # Segundos

    # ==========================================
    # FASE 0: CUESTIONARIO DE INGRESO (CERTIFICACIÓN)
    # ==========================================
    if st.session_state.fase == 0:
        st.title("📝 Fase 0: Certificación de Automatización")
        st.info("Para acceder al SCADA de producción, el equipo debe demostrar sus conocimientos en sistemas de control y automatización.")
        
        with st.form("form_cuestionario"):
            st.subheader("Examen de Ingreso al Cuarto de Control")
            
            q1 = st.radio("1. ¿Cuál es la diferencia principal entre un Lazo Abierto y un Lazo Cerrado?", [
                "a) El lazo cerrado usa motores más grandes.",
                "b) El lazo cerrado cuenta con retroalimentación (sensores) para corregir el error.",
                "c) El lazo abierto es más preciso y costoso."
            ])
            
            q2 = st.radio("2. ¿Qué significan las siglas PLC?", [
                "a) Panel Lógico de Control",
                "b) Procesador Local de Corriente",
                "c) Controlador Lógico Programable"
            ])
            
            q3 = st.radio("3. Una señal que varía de forma continua en el tiempo (ej. 4-20mA o 0-10V) se conoce como:", [
                "a) Señal Digital",
                "b) Señal Analógica",
                "c) Señal Binaria"
            ])
            
            q4 = st.radio("4. Dispositivo encargado de convertir una variable física (presión, temperatura) en una señal eléctrica para el PLC:", [
                "a) Actuador",
                "b) Contactor",
                "c) Sensor / Transductor"
            ])
            
            q5 = st.radio("5. ¿Qué componente actúa como el 'músculo' del sistema (ej. válvulas, motores, cilindros neumáticos)?", [
                "a) Actuador",
                "b) Sensor",
                "c) HMI"
            ])

            q6 = st.radio("6. En un sistema de control, ¿qué significan las siglas SCADA?", [
                "a) Sistema Central de Acción y Distribución Analógica",
                "b) Supervisión, Control y Adquisición de Datos",
                "c) Sensores, Controladores y Actuadores De Automatización"
            ])

            q7 = st.radio("7. ¿Qué tipo de tecnología de sensor es ideal para medir el nivel de un líquido altamente corrosivo sin tocarlo?", [
                "a) Flotador mecánico de acero.",
                "b) Sensor Ultrasónico o de Radar.",
                "c) Sensor de presión diferencial en el fondo."
            ])

            q8 = st.radio("8. La pantalla interactiva en la puerta del tablero que permite al operario ver y controlar el proceso localmente se llama:", [
                "a) SCADA",
                "b) PLC",
                "c) HMI (Interfaz Humano-Máquina)"
            ])

            q9 = st.radio("9. Un dispositivo electromecánico que usa una señal de baja potencia (24V) para cerrar un circuito de alta potencia (220V) es:", [
                "a) Un Relé / Contactor",
                "b) Un Fusible",
                "c) Un Variador de Frecuencia"
            ])

            q10 = st.radio("10. En un controlador PID, ¿cuál es la función principal de la acción Integral (I)?", [
                "a) Reaccionar a cambios bruscos futuros.",
                "b) Eliminar el error en estado estacionario (hacer que el valor llegue exactamente al Setpoint).",
                "c) Encender y apagar el actuador rápidamente."
            ])

            submit_examen = st.form_submit_button("✅ Calificar y Solicitar Acceso al SCADA", type="primary")

            if submit_examen:
                puntaje = 0
                if "b)" in q1: puntaje += 1
                if "c)" in q2: puntaje += 1
                if "b)" in q3: puntaje += 1
                if "c)" in q4: puntaje += 1
                if "a)" in q5: puntaje += 1
                if "b)" in q6: puntaje += 1
                if "b)" in q7: puntaje += 1
                if "c)" in q8: puntaje += 1
                if "a)" in q9: puntaje += 1
                if "b)" in q10: puntaje += 1

                if puntaje >= 8:
                    st.success(f"🎉 ¡Aprobado! Puntaje: {puntaje}/10. Acceso concedido al cuarto de control.")
                    time.sleep(2)
                    st.session_state.fase = 1
                    st.rerun()
                else:
                    st.error(f"❌ Reprobado. Puntaje: {puntaje}/10. Se requiere mínimo 8/10 para operar la planta. Repasen los conceptos e intenten de nuevo.")

    # ==========================================
    # FASE 1: INGENIERÍA Y SETUP DE PLANTA
    # ==========================================
    elif st.session_state.fase == 1:
        st.title("🏭 Fase 1: Setup del Cuarto de Control")
        st.info("Configuración del SCADA Central. Ingrese los datos del turno.")
        
        with st.form("form_setup"):
            col_e1, col_e2 = st.columns(2)
            empresa = col_e1.text_input("Nombre del Equipo / Grupo:")
            jefe_turno = col_e2.text_input("Ingeniero de Turno:")
            
            tiempo_simulacion = st.selectbox("Duración de la Simulación en Tiempo Real:", [
                "10 Minutos (Recomendado para visualización rápida)", 
                "20 Minutos", 
                "60 Minutos (Turno completo)"
            ])
            
            if st.form_submit_button("✅ Iniciar Producción Continua"):
                if empresa and jefe_turno:
                    # Extraer el número de minutos del texto seleccionado
                    minutos = int(tiempo_simulacion.split(" ")[0])
                    st.session_state.duracion_simulacion = minutos * 60
                    
                    st.session_state.datos_planta = {
                        "Empresa": empresa, "Gerente": jefe_turno, 
                        "Fecha_Emision": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.inicio_real = datetime.now()
                    st.session_state.ultima_actualizacion = datetime.now()
                    st.session_state.fase = 2
                    st.rerun()
                else:
                    st.error("⚠️ Ingrese el Nombre del Equipo y el Ingeniero.")

    # ==========================================
    # FASE 2: SIMULACIÓN SCADA ACTIVA (PRODUCCIÓN CONTINUA)
    # ==========================================
    elif st.session_state.fase == 2:
        if st.session_state.inicio_real is None: return
        
        segundos_reales = (datetime.now() - st.session_state.inicio_real).total_seconds()
        tiempo_limite = st.session_state.duracion_simulacion
        
        if segundos_reales >= tiempo_limite:
            st.session_state.fase = 3
            st.rerun()

        ahora = datetime.now()
        delta_segundos = (ahora - st.session_state.ultima_actualizacion).total_seconds()
        st.session_state.ultima_actualizacion = ahora
        
        # Ajuste dinámico del consumo para que los tanques se vacíen según el tiempo elegido
        factor_velocidad = 3600 / tiempo_limite
        consumo_aceite_seg = 3.5 * factor_velocidad
        consumo_metanol_seg = 0.8 * factor_velocidad
        prod_biodiesel_seg = 4.0 * factor_velocidad
        
        if st.session_state.estado_plc == "🟢 RUN":
            if st.session_state.aceite_lts > 0 and st.session_state.metanol_lts > 0:
                st.session_state.aceite_lts -= consumo_aceite_seg * delta_segundos
                st.session_state.metanol_lts -= consumo_metanol_seg * delta_segundos
                st.session_state.biodiesel_prod += prod_biodiesel_seg * delta_segundos
                st.session_state.utilidad_cop += (prod_biodiesel_seg * delta_segundos * 1500)
            else:
                st.session_state.estado_plc = "🔴 ALARMA: Falta de Materia Prima"

        # --- ENCABEZADO SCADA ---
        
        c_head1, c_head2 = st.columns([2, 1])
        c_head1.title(f"🖥️ SCADA Central | Planta: {st.session_state.datos_planta['Empresa']}")
        
        tiempo_restante = max(0, tiempo_limite - segundos_reales)
        mins_rest = int(tiempo_restante // 60)
        segs_rest = int(tiempo_restante % 60)
        c_head2.error(f"⏱️ **TIEMPO DE TURNO: {mins_rest:02d}:{segs_rest:02d}**")

        st.progress(min(1.0, segundos_reales / tiempo_limite), text="Progreso del Turno Automático")
        st.divider()

        col_izq, col_der = st.columns([1, 1])

        # === COLUMNA IZQUIERDA: CÁMARAS Y NIVELES ===
        with col_izq:
            st.subheader("📹 Monitoreo Visual del Proceso")
            if os.path.exists("planta_activa.mp4"):
                st.video("planta_activa.mp4", autoplay=True, loop=True, muted=True)
            elif os.path.exists("planta_activa.gif"):
                st.image("planta_activa.gif", use_container_width=True)
            else:
                st.info("🎥 Planta Activa (Funcionando correctamente en Lazo Cerrado).")

        # === COLUMNA DERECHA: INDICADORES ===
        with col_der:
            st.subheader("🎚️ Instrumentación y Niveles")
            pct_aceite = max(0.0, min(100.0, (st.session_state.aceite_lts / 20000) * 100))
            st.write(f"🛢️ Aceite Vegetal ({st.session_state.aceite_lts:,.0f} L)")
            st.progress(pct_aceite / 100.0)
            
            pct_metanol = max(0.0, min(100.0, (st.session_state.metanol_lts / 5000) * 100))
            st.write(f"🧪 Metanol ({st.session_state.metanol_lts:,.0f} L)")
            st.progress(pct_metanol / 100.0)
            
            pct_bio = min(100.0, (st.session_state.biodiesel_prod / 25000) * 100)
            st.write(f"🟢 Producto: Biodiesel ({st.session_state.biodiesel_prod:,.0f} L)")
            st.progress(pct_bio / 100.0)

            st.markdown("---")
            st.subheader("📊 Indicadores Financieros")
            c1, c2 = st.columns(2)
            c1.metric("Estado PLC Master", st.session_state.estado_plc)
            c2.metric("Utilidad Proyectada", f"${st.session_state.utilidad_cop:,.0f} COP")

        # Actualización continua visual
        if st.session_state.estado_plc == "🟢 RUN":
            time.sleep(1.0)
            st.rerun()

    # ==========================================
    # FASE 3: DESCARGA DE REPORTES
    # ==========================================
    elif st.session_state.fase == 3:
        st.success("🏁 ¡Turno Finalizado!")
        st.header(f"📑 Entrega de Turno: {st.session_state.datos_planta.get('Empresa', 'Grupo')}")
        
        datos_prod = {
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Empresa": st.session_state.datos_planta.get('Empresa', 'N/A'),
            "Ingeniero_Turno": st.session_state.datos_planta.get('Gerente', 'N/A'),
            "Biodiesel_Producido_Lts": round(st.session_state.biodiesel_prod, 1),
            "Utilidad_Generada_COP": st.session_state.utilidad_cop,
            "Estado_Final_Planta": st.session_state.estado_plc
        }
        df_prod = pd.DataFrame([datos_prod])
        csv_prod = df_prod.to_csv(index=False).encode('utf-8')

        c_res1, c_res2 = st.columns(2)
        c_res1.metric("Utilidad Generada (COP)", f"${st.session_state.utilidad_cop:,.0f}")
        c_res2.metric("Producción Total", f"{st.session_state.biodiesel_prod:,.0f} Lts")

        st.markdown("---")
        st.download_button("📥 Descargar Reporte de Producción (.csv)", data=csv_prod, file_name=f"Reporte_{st.session_state.datos_planta.get('Empresa','Grp')}.csv", mime='text/csv')
            
        if st.button("Reiniciar Sistema"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    app()