erDiagram
    campaigns {
        uuid id PK FK
        datetime created_at
        autostring unique_name
        autostring title
        autostring description
        autostring year
        datetime updated_at
        uuid region_id
    }
    llm_provider_config {
        integer id PK
        autostring provider
        autostring api_key
        autostring model
        boolean is_configured
        datetime last_validated
        datetime created_at
        datetime updated_at
    }
    match_results {
        integer id PK FK
        integer ocr_result_id
        integer matcher_job_id
        integer rank
        integer voter_id
        float similarity_score
        enum confidence_level
        json field_scores
        datetime created_at
    }
    matcher_jobs {
        integer id PK FK
        uuid campaign_id
        enum current_status
        autostring provider_name
        autostring provider_model
        boolean force_reprocess
        integer cached_ocr_count
        integer new_ocr_count
        datetime started_on
        datetime updated_on
        datetime ended_on
        float ocr_duration_seconds
        float matching_duration_seconds
        json error_data
        json success_data
        integer started_by
        datetime created_at
    }
    ocr_jobs {
        integer id PK FK
        integer matcher_job_id
        autostring provider_job_id
        integer ocr_model_id
        enum status
        datetime started_on
        datetime updated_on
        datetime ended_on
        json error_data
        json success_data
        datetime created_at
    }
    ocr_models {
        integer id PK FK
        autostring unique_name
        autostring display_name
        integer provider_id
        datetime created_at
    }
    ocr_providers {
        integer id PK
        autostring unique_name
        autostring display_name
        datetime created_at
    }
    ocr_results {
        integer id PK FK
        integer crop_id
        integer ocr_job_id
        integer ocr_index
        json extracted_text
        float confidence_score
        json raw_response
        datetime created_at
    }
    petition_crops {
        integer id PK FK
        integer scan_id
        integer crop_index
        autostring stored_path
        json crop_coordinates
        integer page_number
        datetime created_at
    }
    petition_scans {
        integer id PK FK
        uuid campaign_id
        autostring original_filename
        autostring stored_path
        autostring file_hash
        integer file_size
        integer page_count
        datetime uploaded_at
        integer uploaded_by
    }
    regions {
        uuid id PK
        autostring region_key
        autostring region_name
        autostring country_code
    }
    registered_voters {
        integer id PK FK
        uuid region_id
        json name_data
        json address_data
        json other_field_data
        datetime created_at
        datetime updated_at
        autostring data_hash
        datetime first_seen_at
        datetime last_seen_at
        uuid first_upload_id
        uuid last_upload_id
    }
    sessions {
        integer id PK FK
        uuid campaign_id
        autostring name
        float session_type
        json snapshot_data
        datetime created_at
        datetime updated_at
    }
    users {
        integer id PK
        autostring email
        autostring name
        datetime created_at
    }
    voter_list_uploads {
        uuid id PK FK
        uuid region_id
        autostring original_filename
        integer file_size
        integer row_count
        enum status
        datetime uploaded_at
        datetime superseded_at
        uuid superseded_by
    }

    campaigns ||--o{ regions : id
    match_results ||--o{ registered_voters : id
    matcher_jobs ||--o{ users : id
    ocr_jobs ||--o{ ocr_models : id
    ocr_models ||--o{ ocr_providers : id
    ocr_results ||--o{ petition_crops : id
    petition_crops ||--o{ petition_scans : id
    petition_scans ||--o{ users : id
    registered_voters ||--o{ voter_list_uploads : id
    sessions ||--o{ campaigns : id
    voter_list_uploads ||--o{ regions : id
