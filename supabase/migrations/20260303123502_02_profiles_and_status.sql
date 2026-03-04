--Logic: Identity first, then the high-frequency state.
CREATE TABLE profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('customer', 'barber')),
  bio TEXT,
  rating DECIMAL(3,2) DEFAULT 5.00 CHECK (rating >= 0 AND rating <= 5),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE merchant_status (
  barber_id UUID REFERENCES profiles(id) ON DELETE CASCADE PRIMARY KEY,
  is_online BOOLEAN DEFAULT false,
  last_location GEOGRAPHY(POINT, 4326),
  battery_level INTEGER,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_merchant_location ON merchant_status USING GIST (last_location);

-- The Auto-Status Trigger
CREATE OR REPLACE FUNCTION handle_new_barber_status()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.role = 'barber' THEN
    INSERT INTO public.merchant_status (barber_id) VALUES (NEW.id);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_barber_created
  AFTER INSERT ON profiles
  FOR EACH ROW EXECUTE PROCEDURE handle_new_barber_status();