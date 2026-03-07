-- Enable cron scheduler
create extension if not exists pg_cron;


-- main func
create or replace function public.expire_old_auctions()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  updated_count integer;
begin
  update public.auctions
  set status = 'expired'
  where status = 'open'
    and expires_at <= now();

  get diagnostics updated_count = row_count;
  return updated_count;
end;
$$;


-- remove prev func/jobs
do $$
begin
  if exists (
    select 1
    from cron.job
    where jobname = 'expire-auctions-job'
  ) then
    perform cron.unschedule(jobid)
    from cron.job
    where jobname = 'expire-auctions-job';
  end if;
end
$$;


select cron.schedule(
  'expire-auctions-job',
  '* * * * *',
  $$select public.expire_old_auctions();$$
);