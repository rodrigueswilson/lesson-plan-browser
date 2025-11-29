-- Update RLS policies so that the backend (service_role key) can read/write data
-- while still enforcing per-user access when requests originate from anon keys.
--
-- Run this script separately inside each Supabase project (Wilson / Daniela).

-------------------------------------------------------------------------------
-- Helper function: ownership lookup for weekly_plans
-------------------------------------------------------------------------------
create or replace function public.weekly_plan_owned_by_current_user(plan_text text)
returns boolean
language sql
security definer
stable
as $$
    select
        auth.role() = 'service_role'
        or exists (
            select 1
            from public.weekly_plans wp
            where wp.id = plan_text
              and wp.user_id = auth.uid()::text
        );
$$;

-------------------------------------------------------------------------------
-- users
-------------------------------------------------------------------------------
alter table public.users enable row level security;

drop policy if exists "users_self_rw" on public.users;

create policy "users_self_rw"
    on public.users
    for all
    using (
        auth.role() = 'service_role'
        or id = auth.uid()::text
    )
    with check (
        auth.role() = 'service_role'
        or id = auth.uid()::text
    );

-------------------------------------------------------------------------------
-- class_slots
-------------------------------------------------------------------------------
alter table public.class_slots enable row level security;

drop policy if exists "class_slots_owner_rw" on public.class_slots;

create policy "class_slots_owner_rw"
    on public.class_slots
    for all
    using (
        auth.role() = 'service_role'
        or user_id = auth.uid()::text
    )
    with check (
        auth.role() = 'service_role'
        or user_id = auth.uid()::text
    );

-------------------------------------------------------------------------------
-- weekly_plans
-------------------------------------------------------------------------------
alter table public.weekly_plans enable row level security;

drop policy if exists "weekly_plans_owner_rw" on public.weekly_plans;

create policy "weekly_plans_owner_rw"
    on public.weekly_plans
    for all
    using (
        auth.role() = 'service_role'
        or user_id = auth.uid()::text
    )
    with check (
        auth.role() = 'service_role'
        or user_id = auth.uid()::text
    );

-------------------------------------------------------------------------------
-- performance_metrics
-------------------------------------------------------------------------------
alter table public.performance_metrics enable row level security;

drop policy if exists "performance_metrics_plan_owner_rw" on public.performance_metrics;

create policy "performance_metrics_plan_owner_rw"
    on public.performance_metrics
    for all
    using (
        auth.role() = 'service_role'
        or weekly_plan_owned_by_current_user(plan_id)
    )
    with check (
        auth.role() = 'service_role'
        or weekly_plan_owned_by_current_user(plan_id)
    );

-------------------------------------------------------------------------------
-- schedules
-------------------------------------------------------------------------------
alter table public.schedules enable row level security;

drop policy if exists "schedules_owner_rw" on public.schedules;

create policy "schedules_owner_rw"
    on public.schedules
    for all
    using (
        auth.role() = 'service_role'
        or user_id = auth.uid()::text
    )
    with check (
        auth.role() = 'service_role'
        or user_id = auth.uid()::text
    );

