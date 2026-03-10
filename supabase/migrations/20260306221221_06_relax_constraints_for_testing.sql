-- Relax the profile -> auth.users link so we can create a profile manually
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_id_fkey;
