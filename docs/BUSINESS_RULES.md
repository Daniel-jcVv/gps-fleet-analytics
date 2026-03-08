# Reglas de Negocio - GPS Fleet Analytics

  ## Fuente
  - Archivo: data_gps/rev1/data revision-resumen gps volvo/Informe_de_viaje-20220201-0600 ENE
  22.xlsx

  ## Constantes
  - Rendimiento combinado: 17.23 km/l (varia segun automovil)
  - Precio gasolina: $23.24 MXN/l (marzo 2026, Magna promedio nacional)

  ## Alertas
  - Actividad despues de 19:00 hrs a 07:00 hrs

  ## Limites km/mes
  - Verde: < 3000 km/mes
  - Amarillo: 3000 - 6000 km/mes
  - Rojo: > 6000 km/mes

  ## Formulas combustible
  - Gasolina gastada = distancia / 17.23
  - Costo = gasolina gastada * 23.24
  - Km de mas = total - limite