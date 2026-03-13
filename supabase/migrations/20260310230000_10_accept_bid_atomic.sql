create or replace function public.accept_bid_for_auction(
  p_auction_id uuid,
  p_bid_id uuid
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_auction_status text;
  v_bid_status text;
begin
  select status
  into v_auction_status
  from auctions
  where id = p_auction_id;

  if not found then
    raise exception 'Auction not found';
  end if;

  if v_auction_status <> 'open' then
    raise exception 'Auction is not open for acceptance';
  end if;

  select status
  into v_bid_status
  from bids
  where id = p_bid_id
    and auction_id = p_auction_id;

  if not found then
    raise exception 'Bid not found for this auction';
  end if;

  if v_bid_status <> 'pending' then
    raise exception 'Bid is not pending';
  end if;

  update bids
  set status = 'accepted'
  where id = p_bid_id
    and auction_id = p_auction_id
    and status = 'pending';

  if not found then
    raise exception 'Failed to accept winning bid';
  end if;

  update bids
  set status = 'rejected'
  where auction_id = p_auction_id
    and id <> p_bid_id
    and status = 'pending';

  update auctions
  set status = 'accepted',
      winning_bid_id = p_bid_id
  where id = p_auction_id
    and status = 'open';

  if not found then
    raise exception 'Failed to update auction';
  end if;
end;
$$;
