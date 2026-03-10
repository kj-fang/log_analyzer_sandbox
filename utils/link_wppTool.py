import subprocess
import os
import time
import traceback
from .wpp_ddd_parser import wpp_ddd_parser_run


socketio = None

def emit_log(msg):
    """Emit log message to frontend via SocketIO + optionally print to console"""
    if socketio:
        socketio.emit('wpp_log', {'data': msg}, namespace='/progress')  # Ensure the correct namespace is used

    #print(msg)

def run_wpp_and_check(etl_file):
    """Run .bat logic for WPP processing (through wrapped Python module) and send logs"""
    #emit_log(f"[{time.strftime('%H:%M:%S')}] ⚙️ WPP analysis start：{etl_file}")
    try:
        emit_log("~~~~ Start wpp_ddd_parser ~~~~ ")
        wpp_ddd_parser_run(etl_file)
        emit_log("~~~~ Wpp_ddd done! ~~~~ \n\n")
    except Exception as e:
        emit_log(f"❌ Exception occurred:{e}")
        emit_log(traceback.format_exc())

