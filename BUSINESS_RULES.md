# Reglas de Negocio - GPS Fleet Analytics

  ## Fuente
  - Archivo: data_gps/rev1/data revision-resumen gps volvo/Informe_de_viaje-20220201-0600 ENE
  22.xlsx

  ## Constantes
  - Rendimiento combinado: 17.23 km/l (varia segun automovil)
  - Precio gasolina: $21 MXN/l (enero 2022)

  ## Alertas
  - Inactividad > 2 horas
  - Actividad despues de 19:00 hrs a 07:00 hrs

  ## Limites km/mes
  - Verde: <= 150 km/mes (5 km/dia)
  - Amarillo: <= 300 km/mes (10 km/dia)
  - Rojo: > 300 km/mes (>10 km/dia)

  ## Formulas combustible
  - Gasolina gastada = distancia / 17.23
  - Costo = gasolina gastada * 21
  - Km de mas = total - limite