-- Demo customer
INSERT INTO public.profiles (id, full_name, role, bio)
VALUES (
  '00000000-0000-0000-0000-000000000000',
  'Test Customer',
  'customer',
  'Temporary account for backend integration testing'
)
ON CONFLICT (id) DO UPDATE
SET
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role,
  bio = EXCLUDED.bio;

-- Demo barber
INSERT INTO public.profiles (id, full_name, role, bio)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'Laszlo the Barber',
  'barber',
  'I am the professional responding to requests.'
)
ON CONFLICT (id) DO UPDATE
SET
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role,
  bio = EXCLUDED.bio;

UPDATE public.merchant_status
SET
  is_online = true,
  last_location = ST_SetSRID(ST_MakePoint(19.0402, 47.4979), 4326),
  updated_at = NOW()
WHERE barber_id = '11111111-1111-1111-1111-111111111111';
