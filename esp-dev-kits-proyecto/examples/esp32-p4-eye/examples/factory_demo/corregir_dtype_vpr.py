#!/usr/bin/env python3
"""Ajuste limitado de la Fase 2 VPR: entrada FLOAT32 o INT8.

Conserva el resto de main/app_vpr_runtime.cpp, incluidos logs añadidos a mano.
Crea un respaldo antes de escribir. No requiere bibliotecas Python externas.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

p = argparse.ArgumentParser()
p.add_argument('proyecto', nargs='?', default='.', help='Raíz de factory_demo')
p.add_argument('--verificar', action='store_true', help='Solo comprobar, sin editar archivos')
args = p.parse_args()

archivo = Path(args.proyecto).resolve() / 'main' / 'app_vpr_runtime.cpp'
if not archivo.exists():
    sys.exit(f'ERROR: No existe {archivo}')

src = archivo.read_text(encoding='utf-8')

cambios = [
    (
        'validación de tipo de dato',
        'if (input->dtype != dl::DATA_TYPE_INT8 || input->shape.size() != 4 ||',
        'if ((input->dtype != dl::DATA_TYPE_FLOAT && input->dtype != dl::DATA_TYPE_INT8) ||\n        input->shape.size() != 4 ||',
    ),
    (
        'mensaje de validación',
        '"%s: entrada no es [1,224,224,3] INT8"',
        '"%s: entrada no es [1,224,224,3] FLOAT32/INT8"',
    ),
    (
        'puntero de entrada y escala',
        '''    int8_t *dest = input->get_element_ptr<int8_t>();
    const float inv_scale = DL_RESCALE(input->exponent);''',
        '''    // La entrada del modelo puede ser FLOAT32 aunque sus operaciones
    // internas estén cuantizadas (w8a8). Nunca escribir bytes INT8 en FLOAT32.
    const bool usar_float = (input->dtype == dl::DATA_TYPE_FLOAT);
    float *dest_float = usar_float ? input->get_element_ptr<float>() : nullptr;
    int8_t *dest_int8 = usar_float ? nullptr : input->get_element_ptr<int8_t>();
    const float inv_scale = usar_float ? 1.0f : DL_RESCALE(input->exponent);''',
    ),
    (
        'escritura de píxeles normalizados',
        '                dest[base + ch] = dl::quantize<int8_t>(valor, inv_scale);',
        '''                if (usar_float) {
                    dest_float[base + ch] = valor;  // RGB normalizado a [0, 1]
                } else {
                    dest_int8[base + ch] = dl::quantize<int8_t>(valor, inv_scale);
                }''',
    ),
    (
        'mensaje de estado al usuario',
        'mostrar("Modelo no disponible (PSRAM)", 0, 0, false);',
        'mostrar("Modelo no cargado (ver monitor)", 0, 0, false);',
    ),
    (
        'log detallado de entrada',
        '"%s OK: input exp=%d, salida tipo=%d exp=%d, PSRAM libre=%u KB",\n             nombre, input->exponent, (int)output->dtype, output->exponent,',
        '"%s OK: entrada tipo=%d exp=%d, salida tipo=%d exp=%d, PSRAM libre=%u KB",\n             nombre, (int)input->dtype, input->exponent, (int)output->dtype, output->exponent,',
    ),
]

out = src
for nombre, old, new in cambios:
    n = out.count(old)
    if n != 1:
        if n == 0 and new in out:
            sys.exit('Este ajuste parece ya estar instalado. No se modificó ningún archivo.')
        sys.exit(f'ERROR: {nombre}: se esperaba una coincidencia, encontradas {n}. No se modificó ningún archivo.\nRevisa que sea la Fase 2 original.')
    out = out.replace(old, new, 1)

print(f'Archivo: {archivo}')
print('Verificados 6 cambios: FLOAT32/INT8, escritura correcta, logs y estado.')
if args.verificar:
    print('Verificación completa. NO se modificó ningún archivo.')
    sys.exit(0)

backup = archivo.with_name(archivo.name + '.bak_dtype_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
shutil.copy2(archivo, backup)
archivo.write_text(out, encoding='utf-8')
print('Respaldado:', backup)
print('Actualizado:', archivo)
print('Siguiente paso: idf.py build')
