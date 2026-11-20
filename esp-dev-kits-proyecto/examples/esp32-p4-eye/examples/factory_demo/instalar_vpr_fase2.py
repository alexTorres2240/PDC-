#!/usr/bin/env python3
"""Aplica FASE2 sobre factory_demo con el menu FASE1 ya instalado.
No modifica los .espdl ni borra la UI previa; crea backups de cuatro archivos.
"""
from pathlib import Path
import argparse
from datetime import datetime
import shutil
import sys

MARK = '/* VPR_FASE2: camera -> inferencia a 1 Hz */'

def exact_once(s: str, old: str, new: str, description: str) -> str:
    count = s.count(old)
    if count != 1:
        raise ValueError(f'{description}: esperaba exactamente 1 fragmento, encontre {count}')
    return s.replace(old, new, 1)

p = argparse.ArgumentParser()
p.add_argument('proyecto', nargs='?', default='.', help='Raiz del factory_demo')
p.add_argument('--verificar', action='store_true', help='Solo revisar compatibilidad, sin modificar')
a = p.parse_args()
root = Path(a.proyecto).resolve()
local = Path(__file__).resolve().parent
main = root / 'main'
ui = main / 'ui' / 'ui_extra.c'
video = main / 'app' / 'Video' / 'app_video_stream.c'
c = main / 'main.c'
cm = main / 'CMakeLists.txt'
headers = main / 'ui' / 'ui_extra.h'
files = [ui, video, c, cm, headers]
if not all(x.exists() for x in files):
    sys.exit('ERROR: No es un factory_demo compatible (faltan archivos main/ui o main/app/Video)')
if any(not (local / x).exists() for x in ('app_vpr_runtime.cpp', 'app_vpr_runtime.h')):
    sys.exit('ERROR: faltan app_vpr_runtime.cpp y app_vpr_runtime.h junto a este instalador')

orig = {x: x.read_text(encoding='utf-8') for x in files}
if MARK in orig[video] or 'vpr_runtime_preload();' in orig[c]:
    sys.exit('FASE2 ya parece instalada. No se realizaron cambios.')
if 'UI_PAGE_VPR' not in orig[headers] or 'ui_extra_vpr_set_coordinates' not in orig[ui]:
    sys.exit('ERROR: Primero instala y prueba el menu VPR FASE1')
if 'target_add_aligned_binary_data' not in orig[cm] or 'cnn_classificacion' not in orig[cm] or 'cnn_regresion' not in orig[cm]:
    sys.exit('ERROR: CMakeLists.txt no contiene las dos CNN integradas. Revisa las rutas de modelos.')

try:
    changed = {}
    v = orig[video]
    v = exact_once(v, '#include "app_video_stream.h"', '#include "app_video_stream.h"\n#include "app_vpr_runtime.h"', 'include de video')
    anchor = '''    // Process frame for AI detection if we're on the AI detection page'''
    v = exact_once(v, anchor,
        MARK + '\n'
        '    if (camera_state.flags.is_initialized && ui_extra_get_current_page() == UI_PAGE_VPR) {\n'
        '        /* Frame aun sin el swap de bytes RGB565 destinado a LVGL. */\n'
        '        vpr_runtime_offer_frame((const uint8_t *)camera_buffer.canvas_buf[camera_buf_index],\n'
        '                                BSP_LCD_H_RES, BSP_LCD_V_RES);\n'
        '    }\n\n' + anchor,
        'insercion de captura')
    changed[video] = v

    m = orig[c]
    m = exact_once(m, '#include "ui_extra.h"', '#include "ui_extra.h"\n#include "app_vpr_runtime.h"', 'include main')
    anchor = '''    // Initialize the flashlight'''
    m = exact_once(m, anchor,
        '    /* VPR_FASE2: reservar ambas CNN ANTES de las reservas grandes de CSI */\n'
        '    vpr_runtime_preload();\n\n' + anchor, 'precarga de CNN')
    anchor = '''    ESP_LOGI(TAG, "Application initialization completed");'''
    m = exact_once(m, anchor,
        anchor + '\n    /* VPR_FASE2: tarea de inferencia tras iniciar la camara */\n'
        '    vpr_runtime_start();', 'arranque de tarea')
    # Evitar dejar un test() suelto que pueda aumentar presion de memoria.
    if '    probar_modelo_vpr();' in m:
        m = m.replace('    probar_modelo_vpr();', '    // probar_modelo_vpr(); // desactivado durante VPR_FASE2')
    changed[c] = m

    cmt = orig[cm]
    cmt = exact_once(cmt, 'idf_component_register(SRCS', 'idf_component_register(SRCS "app_vpr_runtime.cpp"', 'registro de CMake')
    changed[cm] = cmt

    uit = orig[ui]
    old = 'UP/DOWN: modelo  MENU: salir\\nSin inferencia en esta fase'
    if old in uit:
        uit = uit.replace(old, 'UP/DOWN: modelo  MENU: salir\\nEsperando 1 fotograma/s', 1)
        changed[ui] = uit

    out_cpp = main / 'app_vpr_runtime.cpp'
    out_h = main / 'app_vpr_runtime.h'
    if out_cpp.exists() or out_h.exists():
        raise ValueError('Hay app_vpr_runtime.cpp/.h ya existentes; no se sobrescribiran')
except Exception as exc:
    sys.exit(f'ERROR (sin modificar): {exc}')

print('Compatibilidad verificada con FASE1.')
print('Archivos a editar:', ', '.join(str(x.relative_to(root)) for x in changed))
print('Archivos nuevos: main/app_vpr_runtime.cpp y main/app_vpr_runtime.h')
if a.verificar:
    print('Modo --verificar: sin cambios.')
    sys.exit(0)

backup = root / ('backup_vpr_fase2_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
backup.mkdir(parents=True, exist_ok=False)
for dest in changed:
    target = backup / dest.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dest, target)
try:
    for dest, content in changed.items():
        dest.write_text(content, encoding='utf-8')
        print('Actualizado:', dest.relative_to(root))
    shutil.copy2(local / 'app_vpr_runtime.cpp', out_cpp)
    shutil.copy2(local / 'app_vpr_runtime.h', out_h)
except Exception as exc:
    print('ERROR al escribir:', exc)
    print('Copia de respaldo en:', backup)
    sys.exit(2)
print('Respaldos:', backup)
print('LISTO: ahora ejecuta idf.py build y valida antes de flashear.')
