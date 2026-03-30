"""
Modulo de Telemetria para T.A.L.O.N.
Mide tiempos de ejecucion y picos de consumo de memoria RAM.
"""
import time
import tracemalloc
import streamlit as st
from contextlib import contextmanager

@contextmanager
def medir_rendimiento(nombre_proceso: str):
    """
    Gestor de contexto que captura el tiempo y la memoria de un bloque de codigo
    y lo almacena en el session_state de Streamlit para su visualizacion.
    """
    if 'telemetria' not in st.session_state:
        st.session_state['telemetria'] = {}
        
    tracemalloc.start()
    tiempo_inicio = time.time()
    
    try:
        yield
    finally:
        tiempo_fin = time.time()
        memoria_actual, memoria_pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        tiempo_total = tiempo_fin - tiempo_inicio
        pico_mb = memoria_pico / (1024 * 1024)
        
        st.session_state['telemetria'][nombre_proceso] = {
            'tiempo_s': tiempo_total,
            'memoria_mb': pico_mb
        }