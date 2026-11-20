#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera la tabla clase -> (X,Y) de cnn_clasificacion_v1.1.

El notebook original crea etiquetas mediante:
  losetas = sorted(set(coordenadas))
  clase_a_coord = {i: coord for i, coord in enumerate(losetas)}

Se admite: 1) exportacion JSON del diccionario exacto del notebook, o
2) directorio del dataset original con carpetas Y (X)_imagenes que contengan
   por lo menos un archivo frame_*.jpg.

El encabezado generado funciona sin cambios en app_vpr_runtime.cpp de Fase 2.
"""
import argparse
import csv
import json
import re
from pathlib import Path
from datetime import datetime

ESPERADAS = 253
PATRON = re.compile(r'(-?\d+)\s*\((-?\d+)\)_imagenes')


def desde_json(ruta):
    objeto = json.loads(ruta.read_text(encoding='utf-8-sig'))
    if not isinstance(objeto, dict):
        raise ValueError('El JSON debe ser un diccionario como {"0": [x,y], ...}.')
    esperado = {str(i) for i in range(ESPERADAS)}
    if set(objeto) != esperado:
        faltantes = sorted(esperado - set(objeto), key=int)
        extras = sorted(set(objeto) - esperado)
        raise ValueError(f'Clases incorrectas: faltantes={faltantes[:10]}, extras={extras[:10]}')
    mapa = []
    for i in range(ESPERADAS):
        xy = objeto[str(i)]
        if not isinstance(xy, (list, tuple)) or len(xy) != 2:
            raise ValueError(f'La clase {i} debe tener exactamente [X,Y]')
        x, y = xy
        if type(x) is not int or type(y) is not int:
            raise ValueError(f'La clase {i} tiene coordenadas no enteras: {xy}')
        mapa.append((x, y))
    return mapa, None


def desde_dataset(ruta):
    if not ruta.is_dir():
        raise ValueError(f'No existe el directorio del dataset: {ruta}')
    coords = []
    fotos = 0
    omitidas = []
    for d in ruta.iterdir():
        if not d.is_dir():
            continue
        m = PATRON.fullmatch(d.name)
        if not m:
            omitidas.append(d.name)
            continue
        archivos = list(d.glob('frame_*.jpg'))
        if not archivos:
            omitidas.append(d.name + ' (sin frame_*.jpg)')
            continue
        y, x = int(m.group(1)), int(m.group(2))
        coords.append((x, y))
        fotos += len(archivos)
    return sorted(set(coords)), {'fotogramas': fotos, 'omitidas': omitidas}


def validar(mapa):
    if len(mapa) != ESPERADAS:
        raise ValueError(
            f'Se esperaban {ESPERADAS} clases y se encontraron {len(mapa)}. '
            'Revisa que estas usando el dataset/mapeo de clasificacion v1.1.'
        )
    if len(set(mapa)) != ESPERADAS:
        raise ValueError('Hay coordenadas repetidas en el mapa. Se detuvo la generacion.')
    for i, (x, y) in enumerate(mapa):
        if not (-32768 <= x <= 32767 and -32768 <= y <= 32767):
            raise ValueError(f'Coordenada de clase {i} fuera de int16: {(x, y)}')
    if mapa != sorted(mapa):
        raise ValueError('El orden no coincide con sorted(set(coordenadas)) del notebook v1.1.')


def escribir(mapa, salida):
    salida.parent.mkdir(parents=True, exist_ok=True)
    lineas = [
        '// GENERADO AUTOMATICAMENTE; NO EDITAR A MANO.',
        '// cnn_clasificacion_v1.1.ipynb: sorted(set(coordenadas))',
        '// Nombre de carpetas: Y (X)_imagenes; entradas: {X,Y}.',
        '#pragma once',
        '#include <stdint.h>',
        f'static const int16_t vpr_clase_a_coord[{ESPERADAS}][2] = {{',
    ]
    lineas.extend(f'    {{{x}, {y}}}, // clase {i}' for i, (x, y) in enumerate(mapa))
    lineas.extend(['};', ''])
    contenido = '\n'.join(lineas)
    if salida.exists():
        if salida.read_text(encoding='utf-8') == contenido:
            print(f'Ya esta actualizado: {salida}')
            return False
        respaldo = salida.with_name(salida.name + '.bak_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
        respaldo.write_bytes(salida.read_bytes())
        print(f'Respaldo del mapa anterior: {respaldo}')
    salida.write_text(contenido, encoding='utf-8', newline='\n')
    print(f'Mapa C/C++ generado: {salida}')
    return True


def main():
    p = argparse.ArgumentParser(description='Convierte las 253 clases de la CNN v1.1 a coordenadas reales (X,Y).')
    grupo = p.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--dataset', type=Path, help='Ruta de la carpeta dataset usada en el entrenamiento')
    grupo.add_argument('--json', type=Path, help='JSON exportado del diccionario clase_a_coord del notebook')
    p.add_argument('--proyecto', type=Path, default=Path('.'), help='Raiz de factory_demo, valor predeterminado: .')
    a = p.parse_args()
    destino = a.proyecto / 'main' / 'vpr_coords_map.h'
    if not (a.proyecto / 'main' / 'app_vpr_runtime.cpp').is_file():
        p.error(f'No encuentro main/app_vpr_runtime.cpp en {a.proyecto}. Ejecuta desde factory_demo.')
    try:
        if a.json:
            mapa, info = desde_json(a.json)
            print(f'Origen: diccionario exacto de entrenamiento en {a.json}')
        else:
            mapa, info = desde_dataset(a.dataset)
            print(f'Origen: carpetas del dataset en {a.dataset}')
        validar(mapa)
        creado = escribir(mapa, destino)
        csv_path = destino.with_name('vpr_coords_map.csv')
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['clase', 'X', 'Y'])
            w.writerows((i, x, y) for i, (x, y) in enumerate(mapa))
        print(f'Tabla para comprobar: {csv_path}')
        print(f'Clases: {len(mapa)}; X={min(x for x,_ in mapa)}..{max(x for x,_ in mapa)}; '
              f'Y={min(y for _,y in mapa)}..{max(y for _,y in mapa)}')
        if info:
            print('Imagenes indexadas:', info['fotogramas'], '(el notebook original uso 84834)')
            if info['fotogramas'] != 84834:
                print('AVISO: el numero de imagenes difiere del notebook; comprueba que es el dataset correcto.')
            if info['omitidas']:
                print('Carpetas omitidas (primeras 10):', ', '.join(info['omitidas'][:10]))
        for i in (0, 64, 118, 150, 215, 244, 249, 252):
            print(f'  Clase {i:3d} -> X={mapa[i][0]}, Y={mapa[i][1]}')
        if creado:
            print('\nSIGUIENTE: idf.py fullclean build; idf.py -p COM38 flash monitor')
        else:
            print('\nEl mapa no cambio; no hace falta recompilar si ya estaba integrado.')
    except (OSError, ValueError, json.JSONDecodeError) as e:
        p.error(str(e))

if __name__ == '__main__':
    main()
