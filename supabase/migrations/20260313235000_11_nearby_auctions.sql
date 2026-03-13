CREATE OR REPLACE FUNCTION get_nearby_open_auctions(
  user_lat FLOAT, 
  user_lng FLOAT, 
  max_radius_meters FLOAT DEFAULT 15000
)
RETURNS TABLE (
  auction_id UUID,
  customer_id UUID,
  service_category TEXT,
  structured_intent JSONB,
  db_created_at TIMESTAMP WITH TIME ZONE,
  service_scheduled_at TIMESTAMP WITH TIME ZONE,
  request_expires_at TIMESTAMP WITH TIME ZONE,
  request_created_at TIMESTAMP WITH TIME ZONE,
  status TEXT,
  distance_meters FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    a.id as auction_id,
    a.customer_id,
    a.service_category,
    a.structured_intent,
    a.db_created_at,
    a.service_scheduled_at,
    a.request_expires_at,
    a.request_created_at,
    a.status,
    ST_Distance(a.location, ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326)::geography) as dist
  FROM auctions a
  WHERE a.status = 'open'
    AND a.request_expires_at > NOW()
    AND ST_DWithin(a.location, ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326)::geography, max_radius_meters)
  ORDER BY dist ASC, a.request_created_at DESC;
END;
$$ LANGUAGE plpgsql;
