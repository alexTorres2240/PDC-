#!/usr/bin/env python3
"""Fase 3: corrige visualizacion X:f Y:f en LVGL (sin cambiar las CNN)."""
import argparse
from pathlib import Path
from datetime import datetime
import shutil
import sys

NUEVA_FUNCION = r'''void ui_extra_vpr_set_coordinates(float x, float y, bool valid)
{
    if (current_page != UI_PAGE_VPR || !vpr_coords_label) return;

    if (!valid) {
        lv_label_set_text(vpr_coords_label, "X: --  Y: --");
    } else if (vpr_modo == VPR_MODO_CLASIFICACION) {
        /* Las coordenadas de una loseta son enteras. */
        int xi = (int)(x + (x >= 0.0f ? 0.5f : -0.5f));
        int yi = (int)(y + (y >= 0.0f ? 0.5f : -0.5f));
        lv_label_set_text_fmt(vpr_coords_label, "X: %d  Y: %d", xi, yi);
    } else {
        /* Regresion: imprimir decimales con enteros para no depender de %f
           en el formateador reducido de LVGL. */
        int x100 = (int)(x * 100.0f + (x >= 0.0f ? 0.5f : -0.5f));
        int y100 = (int)(y * 100.0f + (y >= 0.0f ? 0.5f : -0.5f));
        int ax = x100 < 0 ? -x100 : x100;
        int ay = y100 < 0 ? -y100 : y100;
        lv_label_set_text_fmt(vpr_coords_label, "X: %s%d.%02d  Y: %s%d.%02d",
                              x100 < 0 ? "-" : "", ax / 100, ax % 100,
                              y100 < 0 ? "-" : "", ay / 100, ay % 100);
    }
}'''

def encontrar_funcion(texto: str):
    cabecera = 'void ui_extra_vpr_set_coordinates(float x, float y, bool valid)'
    inicio = texto.find(cabecera)
    if inicio < 0:
        raise ValueError('No se encontro ui_extra_vpr_set_coordinates; verifica que instalaste la Fase 1.')
    apertura = texto.find('{', inicio + len(cabecera))
    if apertura < 0:
        raise ValueError('Falta llave de apertura en la funcion.')
    profundidad = 0
    for i in range(apertura, len(texto)):
        if texto[i] == '{': profundidad += 1
        elif texto[i] == '}':
            profundidad -= 1
            if profundidad == 0:
                return inicio, i + 1
    raise ValueError('La funcion tiene llaves desbalanceadas.')

def main():
    p = argparse.ArgumentParser(description='Corrige X:f Y:f de LVGL en modo VPR.')
    p.add_argument('proyecto', nargs='?', default='.', help='Carpeta raiz de factory_demo')
    p.add_argument('--verificar', action='store_true', help='Solo verificar, no editar archivos')
    args = p.parse_args()
    ruta = Path(args.proyecto).resolve() / 'main' / 'ui' / 'ui_extra.c'
    if not ruta.is_file():
        print(f'ERROR: no existe {ruta}', file=sys.stderr)
        sys.exit(1)
    texto = ruta.read_text(encoding='utf-8')
    inicio, fin = encontrar_funcion(texto)
    anterior = texto[inicio:fin]
    if anterior == NUEVA_FUNCION:
        print('El ajuste ya estaba aplicado. No se modifico ningun archivo.')
        return
    if ('lv_label_set_text_fmt' not in anterior or 'vpr_coords_label' not in anterior
        or 'VPR_MODO_CLASIFICACION' not in anterior):
        print('ERROR: version no reconocida de la funcion. No se modifico.', file=sys.stderr)
        sys.exit(1)
    print('Archivo:', ruta)
    print('Funcion encontrada. Se cambiaran formatos %f por enteros con formato decimal.')
    if args.verificar:
        print('Verificacion correcta. NO se modifico ningun archivo.')
        return
    sufijo = datetime.now().strftime('%Y%m%d_%H%M%S')
    respaldo = ruta.with_name(f'{ruta.name}.bak_display_{sufijo}')
    shutil.copy2(ruta, respaldo)
    ruta.write_text(texto[:inicio] + NUEVA_FUNCION + texto[fin:], encoding='utf-8')
    print('Respaldo:', respaldo)
    print('Corregido:', ruta)
    print('Listo. Ejecuta: idf.py build')

if __name__ == '__main__':
    main()
