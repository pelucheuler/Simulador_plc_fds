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
    .pregunta-box { background-color: #e8f5e9; padding: 15px; border-left: 5px solid #2e7d32; border-radius: 5px; margin-bottom: 20px;}
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
    if 'tiempo_inactivo_seg' not in st.session_state: st.session_state.tiempo_inactivo_seg = 0.0
    if 'calidad_lote' not in st.session_state: st.session_state.calidad_lote = 100.0 

    if 'evento_actual' not in st.session_state: st.session_state.evento_actual = None
    if 'historial_decisiones' not in st.session_state: st.session_state.historial_decisiones = []
    if 'eventos_resueltos' not in st.session_state: st.session_state.eventos_resueltos = []

    # Las 20 Decisiones de Control y Producción para la Simulación SCADA
    LISTA_EVENTOS = [
        {"id": 1, "min_sim": 10, "tema": "Sensores (Nivel)", "titulo": "Discrepancia de Nivel", "desc": "El PLC marca nivel bajo en Metanol, pero el operario ve el tanque al 80%.", "opciones": ["a) Recalibrar el sensor ultrasónico / radar.", "b) Forzar la variable a 80% desde el software del PLC.", "c) Apagar la planta y cambiar el PLC."], "correcta": "a", "img": "evento_01.jpg"},
        {"id": 2, "min_sim": 30, "tema": "Lazos de Control", "titulo": "Oscilación Térmica", "desc": "La temperatura del reactor fluctúa entre 50°C y 70°C con un control ON/OFF. La calidad baja.", "opciones": ["a) Dejarlo así, el ON/OFF es suficiente.", "b) Cambiar a un Lazo Cerrado con control PID.", "c) Instalar un calentador más grande."], "correcta": "b", "img": "evento_02.jpg"},
        {"id": 3, "min_sim": 55, "tema": "Actuadores (VFD)", "titulo": "Ajuste de Caudal", "desc": "Necesitamos reducir el flujo de aceite al 50% para sincronizar la mezcla.", "opciones": ["a) Estrangular la válvula manual de salida.", "b) Reducir el voltaje de la planta completa.", "c) Usar un Variador de Frecuencia (VFD) en la bomba centrífuga."], "correcta": "c", "img": "evento_03.jpg"},
        {"id": 4, "min_sim": 80, "tema": "Normativa / Calidad", "titulo": "Alerta de Humedad", "desc": "Sensor en línea detecta exceso de agua. La norma nacional prohíbe Biodiesel húmedo.", "opciones": ["a) Detener envío a almacenamiento y recircular a la etapa de secado.", "b) Enviar al tanque y mezclarlo para diluir el agua.", "c) Apagar el sensor de humedad."], "correcta": "a", "img": "evento_04.jpg"},
        {"id": 5, "min_sim": 105, "tema": "Sensores (Flujo)", "titulo": "Medición de Mezcla", "desc": "La estequiometría exige precisión exacta en la masa de metanol ingresada.", "opciones": ["a) Usar un medidor de caudal tipo turbina (volumen).", "b) Usar un sensor másico tipo Coriolis.", "c) Calcular al ojo midiendo el tiempo de la bomba."], "correcta": "b", "img": "evento_05.jpg"},
        {"id": 6, "min_sim": 130, "tema": "Sistemas Neumáticos", "titulo": "Caída de Presión de Aire", "desc": "Presión de red neumática cae a 40 psi. Válvula proporcional de vapor no abre al 100%.", "opciones": ["a) El reactor no alcanzará la temperatura, la reacción química será incompleta.", "b) No afecta, el vapor fluye solo.", "c) El PLC compensa la falta de aire inyectando agua."], "correcta": "a", "img": "evento_06.jpg"},
        {"id": 7, "min_sim": 150, "tema": "Eléctrico / Potencia", "titulo": "Sobrecarga de Agitador", "desc": "Motor de 10HP del reactor se dispara. ¿Qué componente del tablero de control actuó?", "opciones": ["a) El sensor ultrasónico.", "b) El Relé Térmico / Guardamotor.", "c) La fuente de 24V DC."], "correcta": "b", "img": "evento_07.jpg"},
        {"id": 8, "min_sim": 175, "tema": "Control de Inventario", "titulo": "Cálculo de Insumos", "desc": "Producimos 100 L/min. Quedan 2000 L de Metanol. Relación Aceite:Metanol es 10:1.", "opciones": ["a) Alcanza para 200 minutos de producción continua.", "b) Alcanza para 20 minutos de producción continua.", "c) Alcanza para 2000 minutos de producción continua."], "correcta": "a", "img": "evento_08.jpg"},
        {"id": 9, "min_sim": 200, "tema": "Control de Personal", "titulo": "Ausencia de Supervisor SCADA", "desc": "El operario del SCADA tuvo una emergencia médica. La planta está en producción continua.", "opciones": ["a) Pasar todos los lazos a MANUAL y que los técnicos operen las válvulas a mano.", "b) Detener la planta inmediatamente.", "c) Mantener el PLC en AUTOMÁTICO pero asignar a alguien a vigilar la pantalla de alarmas."], "correcta": "c", "img": "evento_09.jpg"},
        {"id": 10, "min_sim": 225, "tema": "Control Financiero", "titulo": "Costo de Lucro Cesante", "desc": "Una falla del PLC detuvo la planta 15 min. Se dejaron de producir 1500 Litros. Utilidad esperada: $1000 COP/Litro.", "opciones": ["a) Pérdida de $150.000 COP.", "b) Pérdida de $1.500.000 COP.", "c) Pérdida de $15.000.000 COP."], "correcta": "b", "img": "evento_10.jpg"},
        {"id": 11, "min_sim": 250, "tema": "Estrategia de Control", "titulo": "Tipo de Lazo", "desc": "Para mantener el nivel del tanque de lavado constante mientras entra y sale fluido, requerimos:", "opciones": ["a) Lazo Abierto con temporizador.", "b) Lazo Cerrado (Sensor de nivel + Válvula de control controlada por PLC).", "c) Lazo Neumático puro sin electricidad."], "correcta": "b", "img": "evento_11.jpg"},
        {"id": 12, "min_sim": 275, "tema": "Eficiencia de Producción", "titulo": "Rendimiento (Yield)", "desc": "Se procesaron 5000L de aceite y se obtuvieron 4750L de Biodiesel puro.", "opciones": ["a) Rendimiento del 95%.", "b) Rendimiento del 85%.", "c) Rendimiento del 105%."], "correcta": "a", "img": "evento_12.jpg"},
        {"id": 13, "min_sim": 300, "tema": "SCADA y Comunicaciones", "titulo": "Falla Ethernet Industrial", "desc": "Se pierde la conexión por cable entre el HMI y el PLC. El PLC sigue en RUN.", "opciones": ["a) La planta se detiene automáticamente, causando un desastre.", "b) El PLC sigue controlando el proceso ciego, perdemos visualización pero no producción inmediata.", "c) Las válvulas se abren todas al 100% por seguridad."], "correcta": "b", "img": "evento_13.jpg"},
        {"id": 14, "min_sim": 325, "tema": "Calidad (pH)", "titulo": "Control de Lavado", "desc": "Sensor de pH marca exceso de alcalinidad en el Biodiesel post-reacción.", "opciones": ["a) El PLC debe inyectar más catalizador base (NaOH).", "b) El PLC debe ordenar una dosificación de ácido/agua de lavado para neutralizar.", "c) Ignorar, la alcalinidad es buena para los motores."], "correcta": "b", "img": "evento_14.jpg"},
        {"id": 15, "min_sim": 350, "tema": "Mecánica / Fluidos", "titulo": "Viscosidad Crítica", "desc": "El aceite de palma crudo está muy denso por la madrugada fría. Bomba forzada.", "opciones": ["a) Arrancar la bomba a máxima frecuencia (VFD al 100%).", "b) Activar la resistencia de calentamiento del tanque de aceite por 30 minutos antes de bombear.", "c) Inyectar agua fría para diluir."], "correcta": "b", "img": "evento_15.jpg"},
        {"id": 16, "min_sim": 375, "tema": "Seguridad / Automatización", "titulo": "Alerta de Gases", "desc": "Detector de gases (LEL) indica vapores de metanol en la sala de reactores.", "opciones": ["a) Lógica PLC: Activar paro de emergencia, cerrar válvulas y encender extractores.", "b) Lógica PLC: Aumentar la temperatura del reactor para evaporarlo más rápido.", "c) Lógica PLC: Solo encender una baliza visual, no afectar la producción."], "correcta": "a", "img": "evento_16.jpg"},
        {"id": 17, "min_sim": 400, "tema": "Programación de Producción", "titulo": "Cálculo de Tiempos", "desc": "Gerencia pide 24.000 L urgentes. Nuestra planta controlada produce a razón de 2.000 L/hora.", "opciones": ["a) Planear un turno de 12 horas.", "b) Planear un turno de 24 horas continuas.", "c) Planear un turno de 8 horas con sobremarcha."], "correcta": "a", "img": "evento_17.jpg"},
        {"id": 18, "min_sim": 425, "tema": "Sensores Especializados", "titulo": "Nivel sin Contacto", "desc": "Biodiesel terminado es corrosivo para algunos plásticos. Mejor tecnología para nivel del tanque final:", "opciones": ["a) Flotador mecánico de plástico barato.", "b) Sensor ultrasónico o Radar (sin contacto con el fluido).", "c) Mirilla de vidrio exclusiva para inspección visual."], "correcta": "b", "img": "evento_18.jpg"},
        {"id": 19, "min_sim": 450, "tema": "Actuadores de Precisión", "titulo": "Dosificación de Catalizador", "desc": "Se requieren exactamente 25.5 L/min de metóxido de sodio de forma automatizada.", "opciones": ["a) Válvula de bola accionada manualmente.", "b) Bomba dosificadora (peristáltica o de diafragma) controlada por pulsos del PLC.", "c) Bomba centrífuga de gran capacidad encendida 5 segundos."], "correcta": "b", "img": "evento_19.jpg"},
        {"id": 20, "min_sim": 470, "tema": "Data Analytics / BI", "titulo": "Integración de Datos", "desc": "El SCADA genera reportes de variables y paradas en archivos .CSV", "opciones": ["a) Solo ocupan espacio en el disco duro del PC industrial.", "b) Permiten a Gerencia conectar herramientas como Power BI para analizar OEE y tendencias.", "c) Son archivos que solo los programadores de PLC pueden leer en binario."], "correcta": "b", "img": "evento_20.jpg"}
    ]

    def calcular_tiempo():
        if st.session_state.inicio_real is None: return 0.0, 0.0
        segundos_reales = (datetime.now() - st.session_state.inicio_real).total_seconds()
        if segundos_reales > 3600: segundos_reales = 3600 # Tope 60 minutos
        minutos_simulados = (segundos_reales / 3600.0) * 480.0
        return segundos_reales, minutos_simulados

    # ==========================================
    # FASE 0: CUESTIONARIO DE INGRESO (CERTIFICACIÓN)
    # ==========================================
    if st.session_state.fase == 0:
        st.title("📝 Fase 0: Certificación de Automatización")
        st.info("Para acceder al SCADA interactivo, el equipo debe demostrar sus conocimientos teóricos.")
        
        with st.form("form_cuestionario"):
            st.subheader("Examen de Ingreso al Cuarto de Control")
            
            q1 = st.radio("1. ¿Cuál es la diferencia principal entre un Lazo Abierto y un Lazo Cerrado?", [
                "a) El lazo cerrado usa motores más grandes.",
                "b) El lazo cerrado cuenta con retroalimentación (sensores) para corregir el error.",
                "c) El lazo abierto es más preciso y costoso."
            ], index=None)
            
            q2 = st.radio("2. ¿Qué significan las siglas PLC?", [
                "a) Panel Lógico de Control",
                "b) Procesador Local de Corriente",
                "c) Controlador Lógico Programable"
            ], index=None)
            
            q3 = st.radio("3. Una señal que varía de forma continua en el tiempo (ej. 4-20mA) se conoce como:", [
                "a) Señal Digital",
                "b) Señal Analógica",
                "c) Señal Binaria"
            ], index=None)
            
            q4 = st.radio("4. Dispositivo encargado de convertir una variable física en una señal eléctrica para el PLC:", [
                "a) Actuador",
                "b) Contactor",
                "c) Sensor / Transductor"
            ], index=None)
            
            q5 = st.radio("5. ¿Qué componente actúa como el 'músculo' del sistema (ej. válvulas, motores)?", [
                "a) Actuador",
                "b) Sensor",
                "c) HMI"
            ], index=None)

            q6 = st.radio("6. En un sistema de control, ¿qué significan las siglas SCADA?", [
                "a) Sistema Central de Acción y Distribución Analógica",
                "b) Supervisión, Control y Adquisición de Datos",
                "c) Sensores, Controladores y Actuadores De Automatización"
            ], index=None)

            q7 = st.radio("7. ¿Qué tecnología de sensor es ideal para nivel sin tocar el líquido corrosivo?", [
                "a) Flotador mecánico de acero.",
                "b) Sensor Ultrasónico o de Radar.",
                "c) Sensor de presión diferencial en el fondo."
            ], index=None)

            q8 = st.radio("8. La pantalla interactiva que permite al operario ver y controlar el proceso localmente se llama:", [
                "a) SCADA",
                "b) PLC",
                "c) HMI (Interfaz Humano-Máquina)"
            ], index=None)

            q9 = st.radio("9. Un dispositivo electromecánico que usa baja potencia (24V) para accionar alta potencia (220V) es:", [
                "a) Un Relé / Contactor",
                "b) Un Fusible",
                "c) Un Variador de Frecuencia"
            ], index=None)

            q10 = st.radio("10. En un controlador PID, ¿cuál es la función de la acción Integral (I)?", [
                "a) Reaccionar a cambios bruscos futuros.",
                "b) Eliminar el error estacionario para llegar exactamente al Setpoint.",
                "c) Encender y apagar el actuador rápidamente."
            ], index=None)

            submit_examen = st.form_submit_button("✅ Calificar y Solicitar Acceso al SCADA", type="primary")

            if submit_examen:
                respuestas = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
                if None in respuestas:
                    st.warning("⚠️ Debes responder TODAS las preguntas para enviar el examen.")
                else:
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
                        st.success(f"🎉 ¡Aprobado! Puntaje: {puntaje}/10. Acceso concedido al SCADA.")
                        time.sleep(2)
                        st.session_state.fase = 1
                        st.rerun()
                    else:
                        st.error(f"❌ Reprobado. Puntaje: {puntaje}/10. Mínimo requerido: 8/10. Repasen la teoría.")

    # ==========================================
    # FASE 1: INGENIERÍA Y SETUP DE PLANTA
    # ==========================================
    elif st.session_state.fase == 1:
        st.title("🏭 Fase 1: Ingeniería y Setup de Planta Biodiesel")
        st.info("Configuración del SCADA Central. Ingrese los datos de la empresa.")
        
        with st.form("form_setup"):
            st.subheader("Datos Gerenciales del Turno")
            col_e1, col_e2 = st.columns(2)
            empresa = col_e1.text_input("Nombre del Equipo / Grupo de Ingeniería:")
            jefe_turno = col_e2.text_input("Gerente de Producción (Aprendiz):")
            
            st.subheader("Selección de Tecnologías de Automatización")
            c1, c2, c3 = st.columns(3)
            eq_reactor = c1.checkbox("Reactor CSTR con Lazo Cerrado de Temperatura (PID)", value=True)
            eq_bomba = c2.checkbox("Bomba de Trasiego con Variador de Frecuencia (VFD)")
            eq_sensor = c3.checkbox("Sensores de Nivel Ultrasónico/Radar")
            
            normativa = st.selectbox("Normativa de Calidad Objetivo:", ["ASTM D6751 / EN 14214", "Resolución Nacional Colombiana", "Producción Artesanal"])
            
            if st.form_submit_button("✅ Inicializar SCADA e Iniciar Producción (60 Minutos)"):
                if empresa and jefe_turno:
                    st.session_state.datos_planta = {
                        "Empresa": empresa, "Gerente": jefe_turno, 
                        "Normativa": normativa, "Fecha_Emision": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.inicio_real = datetime.now()
                    st.session_state.ultima_actualizacion = datetime.now()
                    st.session_state.fase = 2
                    st.rerun()
                else:
                    st.error("⚠️ Ingrese el Nombre del Equipo y el Gerente.")

    # ==========================================
    # FASE 2: SIMULACIÓN SCADA ACTIVA (FALLAS Y EVENTOS)
    # ==========================================
    elif st.session_state.fase == 2:
        seg_reales, min_simulados = calcular_tiempo()
        
        if seg_reales >= 3600:
            st.session_state.fase = 3
            st.rerun()

        ahora = datetime.now()
        delta_segundos = (ahora - st.session_state.ultima_actualizacion).total_seconds()
        st.session_state.ultima_actualizacion = ahora
        
        # PROCESO DE PRODUCCIÓN
        if st.session_state.estado_plc == "🟢 RUN" and st.session_state.evento_actual is None:
            consumo_aceite_seg = 3.5 
            consumo_metanol_seg = 0.8
            prod_biodiesel_seg = 4.0 
            
            if st.session_state.aceite_lts > 0 and st.session_state.metanol_lts > 0:
                st.session_state.aceite_lts -= consumo_aceite_seg * delta_segundos
                st.session_state.metanol_lts -= consumo_metanol_seg * delta_segundos
                st.session_state.biodiesel_prod += prod_biodiesel_seg * delta_segundos
                st.session_state.utilidad_cop += (prod_biodiesel_seg * delta_segundos * 1500)
        else:
            st.session_state.tiempo_inactivo_seg += delta_segundos

        # LÓGICA DE DISPARO DE LAS 20 FALLAS
        if st.session_state.evento_actual is None and st.session_state.estado_plc == "🟢 RUN":
            for evento in LISTA_EVENTOS:
                if evento["id"] not in st.session_state.eventos_resueltos:
                    if min_simulados >= evento["min_sim"]:
                        st.session_state.evento_actual = evento
                        st.session_state.estado_plc = "🔴 FAULT (Pausa)"
                        st.rerun()

        # ENCABEZADO
        c_head1, c_head2 = st.columns([2, 1])
        c_head1.title(f"🖥️ SCADA Central | Empresa: {st.session_state.datos_planta['Empresa']}")
        
        tiempo_restante = max(0, 3600 - seg_reales)
        mins_rest = int(tiempo_restante // 60)
        segs_rest = int(tiempo_restante % 60)
        c_head2.error(f"⏱️ **TIEMPO REAL RESTANTE: {mins_rest:02d}:{segs_rest:02d}**")

        horas_sim = min_simulados / 60.0
        st.progress(min(1.0, horas_sim / 8.0), text=f"Jornada Laboral (8 Hrs Simuladas): {horas_sim:.1f} hrs completadas")
        st.divider()

        col_izq, col_der = st.columns([1, 1.2])

        # COLUMNA IZQUIERDA (CÁMARAS Y TANQUES)
        with col_izq:
            st.subheader("📹 Monitoreo Visual Reactivo")
            
            if st.session_state.evento_actual is None:
                if os.path.exists("planta_activa.mp4"):
                    st.video("planta_activa.mp4", autoplay=True, loop=True, muted=True)
                elif os.path.exists("planta_activa.gif"):
                    st.image("planta_activa.gif", use_container_width=True)
                else:
                    st.info("🎥 Planta Activa (Funcionando correctamente).")
            else:
                imagen_evento = st.session_state.evento_actual['img']
                if os.path.exists(imagen_evento):
                    st.image(imagen_evento, use_container_width=True)
                else:
                    st.warning(f"⚠️ Atención Requerida: Falla en {st.session_state.evento_actual['tema']}")

            st.subheader("🎚️ Control de Inventario (Tanques)")
            pct_aceite = max(0.0, min(100.0, (st.session_state.aceite_lts / 20000) * 100))
            st.write(f"🛢️ Aceite Vegetal ({st.session_state.aceite_lts:,.0f} L)")
            st.progress(pct_aceite / 100.0)
            
            pct_metanol = max(0.0, min(100.0, (st.session_state.metanol_lts / 5000) * 100))
            st.write(f"🧪 Metanol ({st.session_state.metanol_lts:,.0f} L)")
            st.progress(pct_metanol / 100.0)
            
            pct_bio = min(100.0, (st.session_state.biodiesel_prod / 25000) * 100)
            st.write(f"🟢 Biodiesel ({st.session_state.biodiesel_prod:,.0f} L)")
            st.progress(pct_bio / 100.0)

        # COLUMNA DERECHA (INDICADORES Y PREGUNTAS)
        with col_der:
            st.subheader("📊 Indicadores de Desempeño (KPIs)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Estado PLC", st.session_state.estado_plc)
            c2.metric("Utilidad", f"${st.session_state.utilidad_cop:,.0f} COP")
            c3.metric("Downtime", f"{(st.session_state.tiempo_inactivo_seg/60):.1f} min")
            c4.metric("Calidad Lote", f"{st.session_state.calidad_lote}%")
            
            st.markdown("---")
            
            if st.session_state.evento_actual:
                ev = st.session_state.evento_actual
                st.markdown(f"<div class='pregunta-box'><b>🚨 EVENTO SCADA: {ev['titulo']}</b><br><br>{ev['desc']}</div>", unsafe_allow_html=True)
                
                with st.form("form_decision"):
                    respuesta_usuario = st.radio("Seleccione la instrucción a enviar:", ev['opciones'])
                    
                    if st.form_submit_button("✅ Confirmar Orden Ejecutiva"):
                        es_correcta = respuesta_usuario.startswith(ev['correcta'])
                        if es_correcta:
                            st.success("Correcto.")
                            st.session_state.calidad_lote = min(100.0, st.session_state.calidad_lote + 1.0)
                        else:
                            st.error("Error de control.")
                            st.session_state.calidad_lote -= 5.0
                            st.session_state.utilidad_cop -= 500000
                        
                        st.session_state.historial_decisiones.append({
                            "Minuto_Simulado": round(min_simulados, 1),
                            "Tema": ev['tema'],
                            "Falla": ev['titulo'],
                            "Decision": respuesta_usuario,
                            "Correcta": "SI" if es_correcta else "NO"
                        })
                        st.session_state.eventos_resueltos.append(ev['id'])
                        st.session_state.evento_actual = None
                        st.session_state.estado_plc = "🟢 RUN"
                        st.rerun()
            else:
                st.success("✅ **SISTEMA AUTOMATIZADO ESTABLE.**")

        if st.session_state.estado_plc == "🟢 RUN" and st.session_state.evento_actual is None:
            time.sleep(1.0)
            st.rerun()

    # ==========================================
    # FASE 3: DESCARGA DE REPORTES
    # ==========================================
    elif st.session_state.fase == 3:
        st.success("🏁 ¡Turno Finalizado!")
        st.header(f"📑 Entrega de Turno: {st.session_state.datos_planta.get('Empresa', 'Grupo')}")
        
        if len(st.session_state.historial_decisiones) > 0:
            df_decisiones = pd.DataFrame(st.session_state.historial_decisiones)
        else:
            df_decisiones = pd.DataFrame([{"Mensaje": "No se tomaron decisiones"}])
        csv_decisiones = df_decisiones.to_csv(index=False).encode('utf-8')
        
        aciertos = sum(1 for d in st.session_state.historial_decisiones if d["Correcta"] == "SI")
        total_preguntas = len(st.session_state.eventos_resueltos)
        
        datos_prod = {
            "Empresa": st.session_state.datos_planta.get('Empresa', 'N/A'),
            "Biodiesel_Producido_Lts": round(st.session_state.biodiesel_prod, 1),
            "Utilidad_Generada_COP": st.session_state.utilidad_cop,
            "Índice_Calidad_Final": f"{st.session_state.calidad_lote}%",
            "Eficiencia_Automatizacion_Aciertos": f"{aciertos} / 20"
        }
        df_prod = pd.DataFrame([datos_prod])
        csv_prod = df_prod.to_csv(index=False).encode('utf-8')

        c_res1, c_res2, c_res3 = st.columns(3)
        c_res1.metric("Utilidad Generada (COP)", f"${st.session_state.utilidad_cop:,.0f}")
        c_res2.metric("Índice de Calidad Final", f"{st.session_state.calidad_lote}%")
        c_res3.metric("Aciertos Automatización", f"{aciertos} / {total_preguntas}")

        st.markdown("---")
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.download_button("1. Descargar Decisiones (.csv)", data=csv_decisiones, file_name="Decisiones.csv", mime='text/csv')
        with c_d2:
            st.download_button("2. Descargar KPI Producción (.csv)", data=csv_prod, file_name="KPI_Produccion.csv", mime='text/csv')
            
        if st.button("Reiniciar Simulador"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    app()