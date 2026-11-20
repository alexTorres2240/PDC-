@echo off
REM Ejecutar SOLO después de idf.py -p COM38 flash (tabla de particiones nueva).
REM REVISAR puerto y nombres antes de grabar. NO usar erase-flash.
python -m esptool --chip esp32p4 -p COM38 -b 460800 write_flash ^
    0xA10000 "C:\Users\Holy Father\Documents\RN - Proyecto de Carrera\export_vpr\espdl\modelo_principal.espdl" ^
    0xB10000 "C:\Users\Holy Father\Documents\RN - Proyecto de Carrera\export_vpr\espdl\modelo_regresion_cluster_0.espdl" ^
    0xC10000 "C:\Users\Holy Father\Documents\RN - Proyecto de Carrera\export_vpr\espdl\modelo_regresion_cluster_1.espdl" ^
    0xD10000 "C:\Users\Holy Father\Documents\RN - Proyecto de Carrera\export_vpr\espdl\modelo_regresion_cluster_2.espdl" ^
    0xE10000 "C:\Users\Holy Father\Documents\RN - Proyecto de Carrera\export_vpr\espdl\modelo_regresion_cluster_3.espdl"
if errorlevel 1 ( echo ERROR AL GRABAR MODELOS & exit /b 1 )
echo Modelos grabados. Reinicia el ESP32-P4 y revisa los logs.
