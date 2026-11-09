#!/usr/bin/env python3
# Agrega pantalla VPR al factory_demo existente sin modificar otros modulos.
# Aplica solo cambios de texto sobre main/ui/ui_extra.c y .h.
from pathlib import Path
import sys, shutil, datetime


def replace_once(content, before, after, context):
    count = content.count(before)
    if count != 1:
        raise RuntimeError(f'{context}: esperaba un unico fragmento (encontre {count}); no cambie archivos.')
    return content.replace(before, after, 1)


def main():
    if len(sys.argv) != 2:
        print('Uso: python instalar_vpr_ui.py "C:\\ruta\\factory_demo"')
        sys.exit(2)
    root = Path(sys.argv[1]).expanduser().resolve()
    path_h = root/'main'/'ui'/'ui_extra.h'
    path_c = root/'main'/'ui'/'ui_extra.c'
    if not (path_h.is_file() and path_c.is_file()):
        sys.exit('ERROR: no se encontro main/ui/ui_extra.c y .h dentro de '+str(root))
    h=path_h.read_text(encoding='utf-8')
    c=path_c.read_text(encoding='utf-8')
    if 'VPR_UI_FASE1' in h or 'VPR_UI_FASE1' in c:
        sys.exit('Este parche ya se aplico. No se modifico nada.')
    h=replace_once(h,'    UI_PAGE_AI_DETECT,      // AI detect page\n    UI_PAGE_MAX',
                   '    UI_PAGE_AI_DETECT,      // AI detect page\n    UI_PAGE_VPR,            // Visual Place Recognition\n    UI_PAGE_MAX','ui_page_t')
    h=replace_once(h,'/* Page management */',
    '''/* VPR_UI_FASE1: API del nuevo menu de localizacion visual.\n   Las funciones que modifican LVGL deben llamarse con el bloqueo de pantalla. */\ntypedef enum {\n    VPR_MODO_CLASIFICACION = 0,\n    VPR_MODO_REGRESION = 1\n} vpr_modo_t;\n\nvpr_modo_t ui_extra_vpr_get_mode(void);\nvoid ui_extra_vpr_set_status(const char *mensaje);\nvoid ui_extra_vpr_set_coordinates(float x, float y, bool valid);\n\n/* Page management */''','header API')

    c=replace_once(c,'static lv_obj_t *ai_mode_label = NULL;',
    '''static lv_obj_t *ai_mode_label = NULL;\n/* VPR_UI_FASE1: solo interfaz, las CNN aun no reciben fotogramas */\nstatic lv_obj_t *vpr_title_label = NULL;\nstatic lv_obj_t *vpr_coords_label = NULL;\nstatic lv_obj_t *vpr_help_label = NULL;\nstatic vpr_modo_t vpr_modo = VPR_MODO_CLASIFICACION;''','variables UI')
    c=replace_once(c, '    {"AI DETECT", UI_PAGE_AI_DETECT},',
                   '    {"AI DETECT", UI_PAGE_AI_DETECT},\n    {"VPR", UI_PAGE_VPR},', 'page_map')
    c=replace_once(c,'static void ui_extra_redirect_to_main_page(void);',
      'static void ui_extra_redirect_to_main_page(void);\nstatic void ui_extra_redirect_to_vpr_page(void);\nstatic void vpr_update_mode_label(void);','forward declarations')
    c=replace_once(c,'"VIDEO MODE", "AI DETECT","ALBUM",',
                   '"VIDEO MODE", "AI DETECT", "VPR", "ALBUM",', 'menu names')
    c=replace_once(c,'        &ui_img_ai_detect_png,\n        &ui_img_album_big_png,',
                   '        &ui_img_ai_detect_png,\n        &ui_img_ai_detect_png, // Icono provisional VPR\n        &ui_img_album_big_png,','menu icons')
    c=replace_once(c,'    // Hide AI mode label if it exists\n',
    '''    if (vpr_title_label) lv_obj_add_flag(vpr_title_label, LV_OBJ_FLAG_HIDDEN);\n    if (vpr_coords_label) lv_obj_add_flag(vpr_coords_label, LV_OBJ_FLAG_HIDDEN);\n    if (vpr_help_label) lv_obj_add_flag(vpr_help_label, LV_OBJ_FLAG_HIDDEN);\n\n    // Hide AI mode label if it exists\n''','hide VPR')

    # Se inserta antes del marcador original, para no alterar las pantallas de la camara.
    c=replace_once(c,'/**\n * @brief Redirect to main page\n */',
    '''/* VPR_UI_FASE1: entorno de seleccion y salida en pantalla. */\nstatic void vpr_update_mode_label(void)\n{\n    if (!vpr_title_label) return;\n    lv_label_set_text(vpr_title_label,\n        vpr_modo == VPR_MODO_CLASIFICACION ? "VPR | CLASIFICACION" : "VPR | REGRESION");\n    if (vpr_coords_label) {\n        lv_label_set_text(vpr_coords_label, "X: --  Y: --");\n    }\n}\n\nstatic void ui_extra_redirect_to_vpr_page(void)\n{\n    current_page = UI_PAGE_VPR;\n    ui_extra_clear_page();\n\n    if (!vpr_title_label) {\n        vpr_title_label = lv_label_create(ui_ScreenCamera);\n        lv_obj_set_style_text_font(vpr_title_label, &lv_font_montserrat_14, 0);\n        lv_obj_set_style_text_color(vpr_title_label, lv_color_hex(0xffffff), 0);\n        lv_obj_set_style_bg_color(vpr_title_label, lv_color_hex(0x162337), 0);\n        lv_obj_set_style_bg_opa(vpr_title_label, LV_OPA_80, 0);\n        lv_obj_set_style_radius(vpr_title_label, 5, 0);\n        lv_obj_set_style_pad_all(vpr_title_label, 5, 0);\n        lv_obj_align(vpr_title_label, LV_ALIGN_TOP_LEFT, 4, 5);\n    }\n    if (!vpr_coords_label) {\n        vpr_coords_label = lv_label_create(ui_ScreenCamera);\n        lv_obj_set_style_text_font(vpr_coords_label, &lv_font_montserrat_16, 0);\n        lv_obj_set_style_text_color(vpr_coords_label, lv_color_hex(0x00ffcc), 0);\n        lv_obj_set_style_bg_color(vpr_coords_label, lv_color_hex(0x162337), 0);\n        lv_obj_set_style_bg_opa(vpr_coords_label, LV_OPA_80, 0);\n        lv_obj_set_style_radius(vpr_coords_label, 5, 0);\n        lv_obj_set_style_pad_all(vpr_coords_label, 5, 0);\n        lv_obj_align(vpr_coords_label, LV_ALIGN_TOP_LEFT, 4, 39);\n    }\n    if (!vpr_help_label) {\n        vpr_help_label = lv_label_create(ui_ScreenCamera);\n        lv_obj_set_style_text_font(vpr_help_label, &lv_font_montserrat_14, 0);\n        lv_obj_set_style_text_color(vpr_help_label, lv_color_hex(0xffffff), 0);\n        lv_obj_set_style_bg_color(vpr_help_label, lv_color_hex(0x162337), 0);\n        lv_obj_set_style_bg_opa(vpr_help_label, LV_OPA_80, 0);\n        lv_obj_set_style_pad_all(vpr_help_label, 4, 0);\n        lv_obj_align(vpr_help_label, LV_ALIGN_BOTTOM_LEFT, 4, -5);\n    }\n    lv_label_set_text(vpr_help_label, "UP/DOWN: modelo  MENU: salir\\nSin inferencia en esta fase");\n    vpr_update_mode_label();\n    lv_obj_clear_flag(vpr_title_label, LV_OBJ_FLAG_HIDDEN);\n    lv_obj_clear_flag(vpr_coords_label, LV_OBJ_FLAG_HIDDEN);\n    lv_obj_clear_flag(vpr_help_label, LV_OBJ_FLAG_HIDDEN);\n}\n\nvpr_modo_t ui_extra_vpr_get_mode(void)\n{\n    return vpr_modo;\n}\n\n/* Llamar solo bajo bsp_display_lock() desde tareas ajenas a LVGL. */\nvoid ui_extra_vpr_set_status(const char *mensaje)\n{\n    if (current_page == UI_PAGE_VPR && vpr_help_label && mensaje) {\n        lv_label_set_text(vpr_help_label, mensaje);\n    }\n}\n\nvoid ui_extra_vpr_set_coordinates(float x, float y, bool valid)\n{\n    if (current_page != UI_PAGE_VPR || !vpr_coords_label) return;\n    if (!valid) {\n        lv_label_set_text(vpr_coords_label, "X: --  Y: --");\n    } else if (vpr_modo == VPR_MODO_CLASIFICACION) {\n        lv_label_set_text_fmt(vpr_coords_label, "X: %.0f  Y: %.0f", x, y);\n    } else {\n        lv_label_set_text_fmt(vpr_coords_label, "X: %.2f  Y: %.2f", x, y);\n    }\n}\n\n/**\n * @brief Redirect to main page\n */''','VPR UI functions')
    c=replace_once(c,'        case UI_PAGE_AI_DETECT:\n            ui_extra_redirect_to_ai_detect_page();\n            break;',
                   '        case UI_PAGE_AI_DETECT:\n            ui_extra_redirect_to_ai_detect_page();\n            break;\n        case UI_PAGE_VPR:\n            ui_extra_redirect_to_vpr_page();\n            break;', 'routing')

    # Two identical switch contexts with the AI_DETECT case; replace within the up/down functions only.
    for name,endname in [('void ui_extra_btn_up(void)','void ui_extra_btn_down(void)'),('void ui_extra_btn_down(void)','void ui_extra_btn_right(void)')]:
        start=c.index(name);end=c.index(endname,start+len(name));sub=c[start:end]
        match='        case UI_PAGE_AI_DETECT:'
        if match not in sub:raise RuntimeError('No AI case in '+name)
        sub=sub.replace(match,'''        case UI_PAGE_VPR:\n            vpr_modo = (vpr_modo == VPR_MODO_CLASIFICACION)\n                         ? VPR_MODO_REGRESION : VPR_MODO_CLASIFICACION;\n            vpr_update_mode_label();\n            break;\n\n        case UI_PAGE_AI_DETECT:''',1)
        c=c[:start]+sub+c[end:]

    start=c.index('void ui_extra_btn_menu(void)');end=c.index('void ui_extra_btn_encoder(void)',start)
    sub=c[start:end]
    sub=replace_once(sub,'    switch(current_page) {\n        case UI_PAGE_MAIN:',
            '    switch(current_page) {\n        case UI_PAGE_VPR:\n            ui_extra_goto_page(UI_PAGE_MAIN);\n            break;\n        case UI_PAGE_MAIN:', 'MENU VPR')
    c=c[:start]+sub+c[end:]

    start=c.index('void ui_extra_btn_encoder(void)');sub=c[start:]
    # VPR no requiere microSD para poder pulsar el encoder.
    sub=replace_once(sub, '    if(!is_sd_card_mounted) {',
        '    if(!is_sd_card_mounted && current_page != UI_PAGE_VPR) {', 'encoder sin SD')
    sub=replace_once(sub,'    switch(current_page) {\n        case UI_PAGE_MAIN:',
      '''    switch(current_page) {\n        case UI_PAGE_VPR:\n            vpr_modo = (vpr_modo == VPR_MODO_CLASIFICACION)\n                         ? VPR_MODO_REGRESION : VPR_MODO_CLASIFICACION;\n            vpr_update_mode_label();\n            break;\n        case UI_PAGE_MAIN:''','ENC VPR')
    c=c[:start]+sub

    # All validations done; back up and write.
    ts=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    for p,content in ((path_h,h),(path_c,c)):
        backup=p.with_name(p.name+'.bak_vpr_'+ts)
        shutil.copy2(p,backup)
        p.write_text(content,encoding='utf-8')
        print('Actualizado:',p)
        print('Respaldo:   ',backup)
    print('Listo. Compilar con idf.py build antes de flashear.')

if __name__=='__main__':
    main()
