ALTER TABLE auctions ADD COLUMN winning_bid_id UUID REFERENCES bids(id) ON DELETE SET NULL;

ALTER TABLE bids ADD COLUMN status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected'));
