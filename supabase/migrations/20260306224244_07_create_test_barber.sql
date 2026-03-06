INSERT INTO public.profiles (id, full_name, role, bio)
VALUES (
  '11111111-1111-1111-1111-111111111111', 
  'Laszlo the Barber', 
  'barber', 
  'I am the professional responding to requests.'
) ON CONFLICT (id) DO NOTHING;

UPDATE public.merchant_status
SET 
  is_online = true,
  last_location = ST_SetSRID(ST_MakePoint(19.0402, 47.4979), 4326) --close to the test user created earlier
WHERE barber_id = '11111111-1111-1111-1111-111111111111';