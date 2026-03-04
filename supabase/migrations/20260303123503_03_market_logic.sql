CREATE TABLE auctions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES profiles(id) NOT NULL,
  service_category TEXT NOT NULL,
  structured_intent JSONB,
  location GEOGRAPHY(POINT, 4326) NOT NULL,
  scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'accepted', 'completed', 'expired', 'cancelled')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE bids (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auction_id UUID REFERENCES auctions(id) ON DELETE CASCADE NOT NULL,
  barber_id UUID REFERENCES profiles(id) NOT NULL,
  price DECIMAL(10,2) NOT NULL CHECK (price > 0),
  eta_minutes INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT unique_barber_bid UNIQUE (auction_id, barber_id)
);