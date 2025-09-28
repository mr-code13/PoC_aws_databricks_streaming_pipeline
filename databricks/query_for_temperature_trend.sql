SELECT
  -- Truncates the event time down to the minute for grouping
  DATE_TRUNC('minute', event_timestamp) AS time_window,
  -- Calculates the fleet-wide average temperature for that minute
  AVG(temperature_c) AS average_fleet_temp
FROM workspace.data_staging.iot_sensor_processed
-- Filter to only show recent data (last hour) for a clear chart
WHERE event_timestamp > NOW() - INTERVAL '60 MINUTES'
GROUP BY 1
ORDER BY time_window DESC;