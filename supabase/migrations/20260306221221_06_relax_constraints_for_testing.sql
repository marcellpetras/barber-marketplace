
-- Relax the profile -> auth.users link so we can create a profile manually
ALTER TABLE public.profiles 
DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- Create a test customer
INSERT INTO public.profiles (id, full_name, role, bio)
VALUES (
  '00000000-0000-0000-0000-000000000000', 
  'Test Customer', 
  'customer', 
  'Temporary account for backend integration testing'
)
ON CONFLICT (id) DO NOTHING;