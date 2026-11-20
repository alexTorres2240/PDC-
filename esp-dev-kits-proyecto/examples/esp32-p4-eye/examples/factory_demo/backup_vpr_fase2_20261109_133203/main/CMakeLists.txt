set(APP_DIR app)

# Collect app core source files
file(GLOB APP_CORE_C_SOURCES ${APP_DIR}/*.c)

# Collect AI module source files
file(GLOB APP_AI_CPP_SOURCES ${APP_DIR}/AI/*.cpp)
file(GLOB APP_AI_C_SOURCES ${APP_DIR}/AI/*.c)

# Collect Video module source files  
file(GLOB APP_VIDEO_C_SOURCES ${APP_DIR}/Video/*.c)

# Combine all app source files
set(APP_ALL_SOURCES 
    ${APP_CORE_C_SOURCES}
    ${APP_AI_CPP_SOURCES} 
    ${APP_AI_C_SOURCES}
    ${APP_VIDEO_C_SOURCES}
)

set(LV_UI_DIR ui)
file(GLOB_RECURSE LV_UI_SOURCES ${LV_UI_DIR}/*.c)

# ==========================================
# MODELOS VPR EN FLASH
# ==========================================

idf_build_get_property(component_targets __COMPONENT_TARGETS)

if ("___idf_espressif__esp-dl" IN_LIST component_targets)
    idf_component_get_property(
        espdl_dir
        espressif__esp-dl
        COMPONENT_DIR
    )
elseif ("___idf_esp-dl" IN_LIST component_targets)
    idf_component_get_property(
        espdl_dir
        esp-dl
        COMPONENT_DIR
    )
else()
    message(FATAL_ERROR "No se encontro el componente ESP-DL")
endif()

set(cmake_dir "${espdl_dir}/fbs_loader/cmake")
include("${cmake_dir}/utilities.cmake")

set(embed_files
    "${CMAKE_CURRENT_LIST_DIR}/../models_vpr/cnn_classificacion_v1_1.espdl"
    "${CMAKE_CURRENT_LIST_DIR}/../models_vpr/cnn_regresion_v1_1.espdl"
)

idf_component_register(SRCS "main.c" "app_vpr.cpp" ${LV_UI_SOURCES} ${APP_ALL_SOURCES} 
                    INCLUDE_DIRS "." ${LV_UI_DIR} ${APP_DIR} ${APP_DIR}/AI ${APP_DIR}/Video
                    REQUIRES esp_driver_ppa nvs_flash human_face_detect pedestrian_detect coco_detect esp_painter)

# ==========================================
# INTEGRAR LOS DOS MODELOS VPR EN FLASH
# ==========================================

foreach(model_file IN LISTS embed_files)

    target_add_aligned_binary_data(
        ${COMPONENT_LIB}
        "${model_file}"
        BINARY
    )

endforeach()