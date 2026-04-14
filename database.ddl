create table public.accounts
(
    id         uuid      default gen_random_uuid() not null
        primary key,
    name       text                                not null,
    is_active  boolean   default true,
    created_at timestamp default CURRENT_TIMESTAMP
);

alter table public.accounts
    owner to admin;

create table public.users
(
    id               uuid      default gen_random_uuid() not null
        primary key,
    external_auth_id text                                not null
        unique,
    account_id       uuid                                not null
        references public.accounts,
    metadata         jsonb     default '{}'::jsonb,
    created_at       timestamp default CURRENT_TIMESTAMP
);

alter table public.users
    owner to admin;

create table public.devices
(
    device_id                 varchar(64) not null
        primary key,
    account_id                uuid        not null
        references public.accounts,
    auth_token_hash           text        not null,
    is_active                 boolean   default false,
    metadata                  jsonb     default '{}'::jsonb,
    last_seen_at              timestamp default CURRENT_TIMESTAMP,
    routing_template_override text
);

alter table public.devices
    owner to admin;

create table public.routing_configs
(
    account_id       uuid not null
        primary key
        references public.accounts,
    default_template text not null,
    updated_at       timestamp default CURRENT_TIMESTAMP
);

alter table public.routing_configs
    owner to admin;

create table public.images
(
    id           uuid      default gen_random_uuid() not null
        primary key,
    device_id    varchar(64)                         not null
        references public.devices,
    status       varchar(32)                         not null,
    captured_at  timestamp default CURRENT_TIMESTAMP,
    image_path   text                                not null,
    context      jsonb     default '{}'::jsonb,
    route_key    text,
    ground_truth annotation_label
);

alter table public.images
    owner to admin;

create index idx_images_device_id
    on public.images (device_id);

create index idx_images_captured_at
    on public.images (captured_at);

create index idx_images_route_key
    on public.images (route_key);

create index idx_images_image_path
    on public.images (image_path);

create table public.inference_results
(
    id                 uuid      default gen_random_uuid() not null
        primary key,
    image_id           uuid                                not null
        references public.images,
    model_id           uuid                                not null,
    anomaly_score      double precision                    not null,
    anomaly_threshold  double precision                    not null,
    is_anomalous       boolean                             not null,
    heatmap_path       text,
    processing_time_ms integer                             not null,
    metadata           jsonb     default '{}'::jsonb,
    processed_at       timestamp default CURRENT_TIMESTAMP
);

alter table public.inference_results
    owner to admin;

create index idx_inference_results_image_id
    on public.inference_results (image_id);

create index idx_inference_results_model_id
    on public.inference_results (model_id);

create index idx_inference_results_is_anomalous
    on public.inference_results (is_anomalous);

create table public.training_groups
(
    id                    uuid      default gen_random_uuid() not null
        primary key,
    account_id            uuid                                not null
        references public.accounts,
    name                  text                                not null,
    member_route_keys     text[]                              not null,
    member_device_ids     text[]    default '{*}'::text[]     not null,
    ml_config             jsonb     default '{}'::jsonb,
    is_active             boolean   default true,
    created_at            timestamp default CURRENT_TIMESTAMP,
    image_count_threshold integer   default 500,
    evolution_steps       integer[] default '{10,50,200}'::integer[],
    current_step_index    integer   default 0
);

alter table public.training_groups
    owner to admin;

create index idx_training_groups_account_id
    on public.training_groups (account_id);

create table public.training_orchestration
(
    group_id            uuid not null
        primary key
        references public.training_groups,
    image_count_current integer     default 0,
    status              varchar(32) default 'IDLE'::character varying,
    last_training_at    timestamp,
    current_job_id      uuid,
    last_model_id       uuid
);

alter table public.training_orchestration
    owner to admin;

create index idx_training_orchestration_status
    on public.training_orchestration (status);

create table public.ml_models
(
    id                uuid      default gen_random_uuid() not null
        primary key,
    name              text                                not null,
    version           text                                not null,
    triton_model_name text                                not null,
    mlflow_run_id     text                                not null,
    source_uri        text                                not null,
    is_active         boolean   default true,
    metadata          jsonb     default '{}'::jsonb,
    created_at        timestamp default CURRENT_TIMESTAMP
);

alter table public.ml_models
    owner to admin;

create table public.image_annotations
(
    id                  uuid      default gen_random_uuid() not null
        primary key,
    image_id            uuid                                not null
        references public.images
            on delete cascade,
    user_id             uuid                                not null
        references public.users,
    inference_result_id uuid
        references public.inference_results,
    label               annotation_label                    not null,
    notes               text,
    geometry_data       jsonb     default '{}'::jsonb,
    created_at          timestamp default CURRENT_TIMESTAMP
);

alter table public.image_annotations
    owner to admin;

create table public.model_performance_metrics
(
    model_id        uuid not null
        primary key
        references public.ml_models,
    true_positives  integer   default 0,
    false_positives integer   default 0,
    true_negatives  integer   default 0,
    false_negatives integer   default 0,
    total_feedback  integer   default 0,
    last_updated    timestamp default CURRENT_TIMESTAMP
);

alter table public.model_performance_metrics
    owner to admin;

create table public.daily_pulse_summaries
(
    id            uuid      default gen_random_uuid() not null
        primary key,
    device_id     varchar(64)                         not null
        references public.devices,
    date          date                                not null,
    normal_count  integer   default 0,
    anomaly_count integer   default 0,
    created_at    timestamp default CURRENT_TIMESTAMP,
    unique (device_id, date)
);

alter table public.daily_pulse_summaries
    owner to admin;

create table public.notification_rules
(
    id         uuid                     default gen_random_uuid() not null
        primary key,
    account_id uuid                                               not null
        references public.accounts
            on delete cascade,
    metadata   jsonb                    default '{}'::jsonb,
    logic_json jsonb                                              not null,
    is_active  boolean                  default true,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

alter table public.notification_rules
    owner to admin;

create table public.notification_channels
(
    id           uuid                     default gen_random_uuid() not null
        primary key,
    rule_id      uuid
        references public.notification_rules
            on delete cascade,
    channel_type varchar(50)                                        not null,
    config       jsonb                                              not null,
    metadata     jsonb                    default '{}'::jsonb,
    created_at   timestamp with time zone default now(),
    updated_at   timestamp with time zone default now()
);

alter table public.notification_channels
    owner to admin;

