#include "app_vpr.h"
#include "dl_model_base.hpp"
#include "esp_log.h"

static const char *TAG = "VPR";

// Direcciones de los modelos integrados en Flash
extern const uint8_t modelo_regresion[]
    asm("_binary_cnn_regresion_v1_1_espdl_start");

extern const uint8_t modelo_clasificacion[]
    asm("_binary_cnn_classificacion_v1_1_espdl_start");

extern "C" void probar_modelo_vpr(void)
{
    ESP_LOGI(TAG, "Cargando CNN de clasificacion desde Flash");

    dl::Model *modelo = new dl::Model(
        (const char *)modelo_clasificacion,
        fbs::MODEL_LOCATION_IN_FLASH_RODATA
    );

    if (modelo == nullptr) {
        ESP_LOGE(TAG, "No se pudo crear el modelo");
        return;
    }

    ESP_LOGI(TAG, "Modelo cargado correctamente");

    esp_err_t resultado = modelo->test();

    if (resultado == ESP_OK) {
        ESP_LOGI(TAG, "Prueba de inferencia correcta");
    } else {
        ESP_LOGE(TAG, "Prueba de inferencia fallida");
    }

    modelo->profile_memory();

    delete modelo;
}