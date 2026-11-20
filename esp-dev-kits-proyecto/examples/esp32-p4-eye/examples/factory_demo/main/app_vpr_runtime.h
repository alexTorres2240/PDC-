#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Cargar ambas CNN una vez, ANTES de inicializar las reservas grandes de la camara. */
void vpr_runtime_preload(void);
/* Crear tarea de inferencia DESPUES de iniciar el flujo de camara. */
void vpr_runtime_start(void);
/* Ofrecer una copia de un frame RGB565 240x240 desde el callback de video. */
void vpr_runtime_offer_frame(const uint8_t *rgb565, int width, int height);

#ifdef __cplusplus
}
#endif
