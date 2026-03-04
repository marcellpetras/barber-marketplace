CREATE OR REPLACE FUNCTION get_eligible_barbers(
  user_lat FLOAT, 
  user_lng FLOAT, 
  max_radius_meters FLOAT DEFAULT 5000
)
RETURNS TABLE (
  barber_id UUID,
  barber_name TEXT,
  distance_meters FLOAT,
  current_rating DECIMAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    p.id, p.full_name,
    ST_Distance(ms.last_location, ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326)::geography) as dist,
    p.rating
  FROM profiles p
  JOIN merchant_status ms ON p.id = ms.barber_id
  WHERE p.role = 'barber'
    AND ms.is_online = true
    AND ms.updated_at > (NOW() - INTERVAL '15 minutes')
    AND ST_DWithin(ms.last_location, ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326)::geography, max_radius_meters)
  ORDER BY dist ASC;
END;
$$ LANGUAGE plpgsql;