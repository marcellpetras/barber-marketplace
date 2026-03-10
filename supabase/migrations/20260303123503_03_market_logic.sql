CREATE TABLE auctions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES profiles(id) NOT NULL,
  service_category TEXT NOT NULL,
  structured_intent JSONB,
  location GEOGRAPHY(POINT, 4326) NOT NULL,
  db_created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), --db load timestamp
  service_scheduled_at TIMESTAMP WITH TIME ZONE, -- when the customer wants the service
  request_expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- when the request expires and can no longer be accepted
  request_created_at TIMESTAMP WITH TIME ZONE NOT NULL, -- when the request was created by the customer
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'accepted', 'completed', 'expired', 'cancelled'))
);

CREATE TABLE bids (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auction_id UUID REFERENCES auctions(id) ON DELETE CASCADE NOT NULL,
  barber_id UUID REFERENCES profiles(id) NOT NULL,
  price DECIMAL(10,2) NOT NULL CHECK (price > 0),
  eta_minutes INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT unique_barber_bid UNIQUE (auction_id, barber_id),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected'))
);

ALTER TABLE auctions
ADD COLUMN winning_bid_id UUID REFERENCES bids(id) ON DELETE SET NULL;
