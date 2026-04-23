create table public.account_usage_counters (
                                               tableoid oid not null,
                                               cmax cid not null,
                                               xmax xid not null,
                                               cmin cid not null,
                                               xmin xid not null,
                                               ctid tid not null,
                                               account_id uuid not null,
                                               period_start timestamp without time zone not null,
                                               period_end timestamp without time zone not null,
                                               inference_count integer default 0,
                                               primary key (account_id, period_start),
                                               foreign key (account_id) references public.accounts (id)
                                                   match simple on update no action on delete cascade
);

create table public.accounts (
                                 tableoid oid not null,
                                 cmax cid not null,
                                 xmax xid not null,
                                 cmin cid not null,
                                 xmin xid not null,
                                 ctid tid not null,
                                 id uuid primary key not null default gen_random_uuid(),
                                 name text not null,
                                 is_active boolean default true,
                                 stripe_customer_id text,
                                 stripe_subscription_id text,
                                 tier_id text default 'FREE'::text,
                                 subscription_status text default 'active'::text,
                                 current_period_end timestamp without time zone,
                                 created_at timestamp without time zone default CURRENT_TIMESTAMP,
                                 foreign key (tier_id) references public.subscription_tiers (id)
                                     match simple on update no action on delete no action
);
create unique index accounts_stripe_customer_id_key on accounts using btree (stripe_customer_id);
create unique index accounts_stripe_subscription_id_key on accounts using btree (stripe_subscription_id);
create index idx_accounts_stripe_customer_id on accounts using btree (stripe_customer_id);

create table public.daily_pulse_summaries (
                                              tableoid oid not null,
                                              cmax cid not null,
                                              xmax xid not null,
                                              cmin cid not null,
                                              xmin xid not null,
                                              ctid tid not null,
                                              id uuid primary key not null default gen_random_uuid(),
                                              device_id character varying(64) not null,
                                              date date not null,
                                              normal_count integer default 0,
                                              anomaly_count integer default 0,
                                              created_at timestamp without time zone default CURRENT_TIMESTAMP,
                                              foreign key (device_id) references public.devices (device_id)
                                                  match simple on update no action on delete no action
);
create unique index daily_pulse_summaries_device_id_date_key on daily_pulse_summaries using btree (device_id, date);

create table public.devices (
                                tableoid oid not null,
                                cmax cid not null,
                                xmax xid not null,
                                cmin cid not null,
                                xmin xid not null,
                                ctid tid not null,
                                device_id character varying(64) primary key not null,
                                account_id uuid not null,
                                auth_token_hash text not null,
                                is_active boolean default false,
                                metadata jsonb default '{}'::jsonb,
                                last_seen_at timestamp without time zone default CURRENT_TIMESTAMP,
                                routing_template_override text,
                                foreign key (account_id) references public.accounts (id)
                                    match simple on update no action on delete no action
);

create table public.image_annotations (
                                          tableoid oid not null,
                                          cmax cid not null,
                                          xmax xid not null,
                                          cmin cid not null,
                                          xmin xid not null,
                                          ctid tid not null,
                                          id uuid primary key not null default gen_random_uuid(),
                                          image_id uuid not null,
                                          user_id uuid not null,
                                          inference_result_id uuid,
                                          label annotation_label not null,
                                          notes text,
                                          geometry_data jsonb default '{}'::jsonb,
                                          created_at timestamp without time zone default CURRENT_TIMESTAMP,
                                          foreign key (image_id) references public.images (id)
                                              match simple on update no action on delete cascade,
                                          foreign key (inference_result_id) references public.inference_results (id)
                                              match simple on update no action on delete no action,
                                          foreign key (user_id) references public.users (id)
                                              match simple on update no action on delete no action
);

create table public.images (
                               tableoid oid not null,
                               cmax cid not null,
                               xmax xid not null,
                               cmin cid not null,
                               xmin xid not null,
                               ctid tid not null,
                               id uuid primary key not null default gen_random_uuid(),
                               device_id character varying(64) not null,
                               status character varying(32) not null,
                               captured_at timestamp without time zone default CURRENT_TIMESTAMP,
                               image_path text not null,
                               context jsonb default '{}'::jsonb,
                               route_key text,
                               ground_truth annotation_label,
                               foreign key (device_id) references public.devices (device_id)
                                   match simple on update no action on delete no action
);
create index idx_images_device_id on images using btree (device_id);
create index idx_images_captured_at on images using btree (captured_at);
create index idx_images_route_key on images using btree (route_key);
create index idx_images_image_path on images using btree (image_path);

create table public.inference_results (
                                          tableoid oid not null,
                                          cmax cid not null,
                                          xmax xid not null,
                                          cmin cid not null,
                                          xmin xid not null,
                                          ctid tid not null,
                                          id uuid primary key not null default gen_random_uuid(),
                                          image_id uuid not null,
                                          model_id uuid not null,
                                          anomaly_score double precision not null,
                                          anomaly_threshold double precision not null,
                                          is_anomalous boolean not null,
                                          heatmap_path text,
                                          processing_time_ms integer not null,
                                          metadata jsonb default '{}'::jsonb,
                                          processed_at timestamp without time zone default CURRENT_TIMESTAMP,
                                          foreign key (image_id) references public.images (id)
                                              match simple on update no action on delete no action,
                                          foreign key (model_id) references public.ml_models (id)
                                              match simple on update no action on delete no action
);
create index idx_inference_results_image_id on inference_results using btree (image_id);
create index idx_inference_results_model_id on inference_results using btree (model_id);
create index idx_inference_results_is_anomalous on inference_results using btree (is_anomalous);

create table public.ml_models (
                                  tableoid oid not null,
                                  cmax cid not null,
                                  xmax xid not null,
                                  cmin cid not null,
                                  xmin xid not null,
                                  ctid tid not null,
                                  id uuid primary key not null default gen_random_uuid(),
                                  name text not null,
                                  version text not null,
                                  triton_model_name text not null,
                                  mlflow_run_id text not null,
                                  source_uri text not null,
                                  is_active boolean default true,
                                  metadata jsonb default '{}'::jsonb,
                                  created_at timestamp without time zone default CURRENT_TIMESTAMP
);

create table public.model_performance_metrics (
                                                  tableoid oid not null,
                                                  cmax cid not null,
                                                  xmax xid not null,
                                                  cmin cid not null,
                                                  xmin xid not null,
                                                  ctid tid not null,
                                                  model_id uuid primary key not null,
                                                  true_positives integer default 0,
                                                  false_positives integer default 0,
                                                  true_negatives integer default 0,
                                                  false_negatives integer default 0,
                                                  total_feedback integer default 0,
                                                  last_updated timestamp without time zone default CURRENT_TIMESTAMP,
                                                  foreign key (model_id) references public.ml_models (id)
                                                      match simple on update no action on delete no action
);

create table public.notification_channels (
                                              tableoid oid not null,
                                              cmax cid not null,
                                              xmax xid not null,
                                              cmin cid not null,
                                              xmin xid not null,
                                              ctid tid not null,
                                              id uuid primary key not null default gen_random_uuid(),
                                              rule_id uuid,
                                              channel_type character varying(50) not null,
                                              config jsonb not null,
                                              metadata jsonb default '{}'::jsonb,
                                              created_at timestamp with time zone default now(),
                                              updated_at timestamp with time zone default now(),
                                              foreign key (rule_id) references public.notification_rules (id)
                                                  match simple on update no action on delete cascade
);

create table public.notification_rules (
                                           tableoid oid not null,
                                           cmax cid not null,
                                           xmax xid not null,
                                           cmin cid not null,
                                           xmin xid not null,
                                           ctid tid not null,
                                           id uuid primary key not null default gen_random_uuid(),
                                           account_id uuid not null,
                                           metadata jsonb default '{}'::jsonb,
                                           logic_json jsonb not null,
                                           is_active boolean default true,
                                           created_at timestamp with time zone default now(),
                                           updated_at timestamp with time zone default now(),
                                           foreign key (account_id) references public.accounts (id)
                                               match simple on update no action on delete cascade
);

create table public.routing_configs (
                                        tableoid oid not null,
                                        cmax cid not null,
                                        xmax xid not null,
                                        cmin cid not null,
                                        xmin xid not null,
                                        ctid tid not null,
                                        account_id uuid primary key not null,
                                        default_template text not null,
                                        updated_at timestamp without time zone default CURRENT_TIMESTAMP,
                                        foreign key (account_id) references public.accounts (id)
                                            match simple on update no action on delete no action
);

create table public.subscription_tiers (
                                           tableoid oid not null,
                                           cmax cid not null,
                                           xmax xid not null,
                                           cmin cid not null,
                                           xmin xid not null,
                                           ctid tid not null,
                                           id text primary key not null,
                                           max_devices integer not null,
                                           inference_limit_monthly integer not null,
                                           retention_days integer not null,
                                           max_ai_level integer not null,
                                           stripe_price_id text,
                                           overage_allowed boolean default false
);

create table public.training_groups (
                                        tableoid oid not null,
                                        cmax cid not null,
                                        xmax xid not null,
                                        cmin cid not null,
                                        xmin xid not null,
                                        ctid tid not null,
                                        id uuid primary key not null default gen_random_uuid(),
                                        account_id uuid not null,
                                        name text not null,
                                        member_route_keys text[] not null,
                                        member_device_ids text[] not null default '{*}'::text[],
                                        ml_config jsonb default '{}'::jsonb,
                                        is_active boolean default true,
                                        created_at timestamp without time zone default CURRENT_TIMESTAMP,
                                        image_count_threshold integer default 500,
                                        evolution_steps integer[] default '{10,50,200}'::integer[],
                                        current_step_index integer default 0,
                                        foreign key (account_id) references public.accounts (id)
                                            match simple on update no action on delete no action
);
create index idx_training_groups_account_id on training_groups using btree (account_id);

create table public.training_orchestration (
                                               tableoid oid not null,
                                               cmax cid not null,
                                               xmax xid not null,
                                               cmin cid not null,
                                               xmin xid not null,
                                               ctid tid not null,
                                               group_id uuid primary key not null,
                                               image_count_current integer default 0,
                                               status character varying(32) default 'IDLE',
                                               last_training_at timestamp without time zone,
                                               current_job_id uuid,
                                               last_model_id uuid,
                                               foreign key (group_id) references public.training_groups (id)
                                                   match simple on update no action on delete no action,
                                               foreign key (last_model_id) references public.ml_models (id)
                                                   match simple on update no action on delete no action
);
create index idx_training_orchestration_status on training_orchestration using btree (status);

create table public.users (
                              tableoid oid not null,
                              cmax cid not null,
                              xmax xid not null,
                              cmin cid not null,
                              xmin xid not null,
                              ctid tid not null,
                              id uuid primary key not null default gen_random_uuid(),
                              external_auth_id text not null,
                              account_id uuid not null,
                              metadata jsonb default '{}'::jsonb,
                              created_at timestamp without time zone default CURRENT_TIMESTAMP,
                              foreign key (account_id) references public.accounts (id)
                                  match simple on update no action on delete no action
);
create unique index users_external_auth_id_key on users using btree (external_auth_id);

