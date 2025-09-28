SELECT
  device_id,
  -- Counts how many times this device has been marked as critical
  COUNT(*) AS critical_count
FROM workspace.data_staging.iot_sensor_processed
-- Only count the critical events
WHERE is_critical = true
-- Look at the last 24 hours of data using the derived TIMESTAMP column
  AND event_timestamp > NOW() - INTERVAL '24 HOURS'
GROUP BY device_id
ORDER BY critical_count DESC;