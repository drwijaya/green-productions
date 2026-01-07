# Entity Relationship Diagram (ERD) - Green Productions

The following diagram illustrates the relationship between the core database tables in the Green Productions system.

```mermaid
erDiagram
    %% Core Users & Employees
    USERS ||--o| EMPLOYEES : "linked_to"
    USERS {
        int id PK
        string username
        string email
        string role
    }
    EMPLOYEES {
        int id PK
        int user_id FK
        string employee_code
        string name
        string department
        string position
    }

    %% CRM & Orders
    CUSTOMERS ||--o{ ORDERS : "places"
    CUSTOMERS {
        int id PK
        string name
        string email
        string phone
    }
    ORDERS ||--o{ DSO : "has_versions"
    ORDERS ||--o{ PRODUCTION_TASKS : "contains_stages"
    ORDERS {
        int id PK
        string order_code
        int customer_id FK
        string model
        string status
        date deadline
    }

    %% DSO (Design & Specs)
    DSO {
        int id PK
        int order_id FK
        int version
        string status
        json components
    }

    %% Production Execution
    PRODUCTION_TASKS ||--o{ QC_SHEETS : "inspected_via"
    PRODUCTION_TASKS {
        int id PK
        int order_id FK
        string task_name
        string process "cutting/sewing/etc"
        int pic_id FK "Employee"
        string status
    }

    %% QC & Defects
    QC_SHEETS ||--o{ DEFECT_LOGS : "logs_defects"
    QC_SHEETS {
        int id PK
        string inspection_code
        int production_task_id FK
        int inspector_id FK "Employee"
        string result "pass/fail"
    }
    DEFECT_LOGS {
        int id PK
        int qc_sheet_id FK
        string defect_type
        string severity
        int reported_by FK "Employee"
        int resolved_by FK "Employee"
    }

    %% Materials Management
    VENDORS ||--o{ MATERIAL_REQUESTS : "supplies"
    VENDORS ||--o{ MATERIALS : "supplies_default"
    VENDORS {
        int id PK
        string name
        string contact_person
    }
    
    MATERIALS {
        int id PK
        string code
        string name
        int stock_qty
    }

    MATERIAL_REQUESTS ||--o{ MATERIAL_REQUEST_ITEMS : "contains"
    MATERIAL_REQUESTS ||--|| MATERIAL_QC_SHEETS : "verified_by"
    ORDERS ||--o{ MATERIAL_REQUESTS : "triggers_request"
    MATERIAL_REQUESTS {
        int id PK
        string request_code
        int vendor_id FK
        int order_id FK
        string status
    }

    MATERIAL_REQUEST_ITEMS {
        int id PK
        int material_request_id FK
        string material_name
        int qty_ordered
    }
    
    MATERIAL_QC_SHEETS {
        int id PK
        int material_request_id FK
        string inspection_code
        string result
    }

    %% Implicit Relations (Foreign Keys to Employee)
    EMPLOYEES ||--o{ PRODUCTION_TASKS : "supervises"
    EMPLOYEES ||--o{ QC_SHEETS : "inspects"
    EMPLOYEES ||--o{ DEFECT_LOGS : "reports/resolves"
```

## Legend

*   **PK**: Primary Key
*   **FK**: Foreign Key
*   **||--o{**: One-to-Many Relationship
*   **||--||**: One-to-One Relationship
*   **||--o|**: One-to-Zero/One Relationship
