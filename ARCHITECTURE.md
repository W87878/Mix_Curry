# 🏗️ 災民補助申請系統 - 系統架構文件

## 📋 目錄

1. [系統架構圖](#系統架構圖)
2. [資料庫架構圖](#資料庫架構圖)
3. [API 路由架構](#api-路由架構)
4. [檔案結構](#檔案結構)
5. [技術堆疊](#技術堆疊)

---

## 系統架構圖

### 整體系統架構 (System Architecture)

```mermaid
graph TB
    subgraph "前端層 Frontend Layer"
        Web[網頁測試介面<br/>test_api.html]
        RestClient[REST Client<br/>test.http]
        ReactApp[React/Vue/Next.js<br/>前端應用]
    end
    
    subgraph "API 層 API Layer - FastAPI"
        Main[main.py<br/>FastAPI Application]
        
        subgraph "路由層 Routers"
            UserRouter[users.py<br/>使用者管理]
            AppRouter[applications.py<br/>申請案件]
            PhotoRouter[photos.py<br/>照片管理]
            ReviewRouter[reviews.py<br/>審核管理]
            CertRouter[certificates.py<br/>數位憑證]
        end
        
        subgraph "服務層 Services"
            StorageService[storage.py<br/>檔案儲存服務]
            GovWalletService[gov_wallet.py<br/>政府憑證服務]
        end
        
        subgraph "資料模型層 Models"
            Models[models.py<br/>Pydantic Models]
            Database[database.py<br/>Database Service]
        end
    end
    
    subgraph "外部服務層 External Services"
        Supabase[(Supabase)]
        
        subgraph "Supabase 服務"
            PostgreSQL[(PostgreSQL<br/>資料庫)]
            Storage[Storage<br/>檔案儲存]
        end
        
        GovAPI[政府數位憑證 API]
        
        subgraph "政府 API"
            IssuerAPI[Issuer API<br/>發行端]
            VerifierAPI[Verifier API<br/>驗證端]
        end
    end
    
    %% 前端到 API 的連接
    Web --> Main
    RestClient --> Main
    ReactApp --> Main
    
    %% API 內部連接
    Main --> UserRouter
    Main --> AppRouter
    Main --> PhotoRouter
    Main --> ReviewRouter
    Main --> CertRouter
    
    UserRouter --> Database
    AppRouter --> Database
    PhotoRouter --> Database
    PhotoRouter --> StorageService
    ReviewRouter --> Database
    CertRouter --> Database
    CertRouter --> StorageService
    CertRouter --> GovWalletService
    
    Database --> Models
    StorageService --> Storage
    GovWalletService --> GovAPI
    
    %% 外部服務連接
    Database --> PostgreSQL
    Storage --> Supabase
    PostgreSQL --> Supabase
    GovAPI --> IssuerAPI
    GovAPI --> VerifierAPI
    
    %% 樣式
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef api fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    
    class Web,RestClient,ReactApp frontend
    class Main,UserRouter,AppRouter,PhotoRouter,ReviewRouter,CertRouter,StorageService,GovWalletService,Models,Database api
    class Supabase,PostgreSQL,Storage,GovAPI,IssuerAPI,VerifierAPI external
```

### 請求處理流程 (Request Flow)

```mermaid
sequenceDiagram
    participant User as 👤 使用者
    participant Frontend as 🌐 前端
    participant FastAPI as 🚀 FastAPI
    participant Router as 📋 Router
    participant Service as ⚙️ Service
    participant DB as 💾 Database
    participant Storage as 📦 Storage
    participant GovAPI as 🏛️ 政府 API
    
    User->>Frontend: 1. 提交申請
    Frontend->>FastAPI: 2. POST /api/v1/applications/
    FastAPI->>Router: 3. 路由到 applications.py
    Router->>Service: 4. 驗證資料
    Service->>DB: 5. 建立申請記錄
    DB-->>Service: 6. 返回申請 ID
    
    User->>Frontend: 7. 上傳照片
    Frontend->>FastAPI: 8. POST /api/v1/photos/upload
    FastAPI->>Router: 9. 路由到 photos.py
    Router->>Storage: 10. 上傳到 Supabase Storage
    Storage-->>Router: 11. 返回檔案 URL
    Router->>DB: 12. 儲存照片記錄
    
    User->>Frontend: 13. 審核核准
    Frontend->>FastAPI: 14. POST /api/v1/reviews/approve/
    FastAPI->>Router: 15. 路由到 reviews.py
    Router->>DB: 16. 更新申請狀態
    Router->>Service: 17. 建立數位憑證
    Service->>GovAPI: 18. 請求政府 API 發行憑證
    GovAPI-->>Service: 19. 返回憑證資料
    Service->>Storage: 20. 生成 QR Code
    Storage-->>Service: 21. 返回 QR Code URL
    Service->>DB: 22. 儲存憑證記錄
    DB-->>Router: 23. 返回完整資料
    Router-->>FastAPI: 24. 返回 API 回應
    FastAPI-->>Frontend: 25. JSON Response
    Frontend-->>User: 26. 顯示結果
```

---

## 資料庫架構圖

### Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ APPLICATIONS : "申請"
    USERS ||--o{ DAMAGE_PHOTOS : "上傳"
    USERS ||--o{ REVIEW_RECORDS : "審核"
    USERS ||--o{ DIGITAL_CERTIFICATES : "發行/驗證"
    
    APPLICATIONS ||--o{ DAMAGE_PHOTOS : "包含"
    APPLICATIONS ||--o{ REVIEW_RECORDS : "記錄"
    APPLICATIONS ||--o{ DIGITAL_CERTIFICATES : "生成"
    APPLICATIONS ||--o{ SUBSIDY_ITEMS : "包含"
    
    USERS {
        uuid id PK
        varchar email UK
        varchar phone
        varchar full_name
        varchar id_number UK
        varchar role
        timestamp created_at
        timestamp updated_at
    }
    
    APPLICATIONS {
        uuid id PK
        varchar case_no UK
        uuid applicant_id FK
        varchar applicant_name
        varchar id_number
        varchar phone
        text address
        date disaster_date
        varchar disaster_type
        text damage_description
        text damage_location
        decimal estimated_loss
        varchar subsidy_type
        decimal requested_amount
        varchar status
        text review_notes
        decimal approved_amount
        timestamp submitted_at
        timestamp reviewed_at
        timestamp completed_at
        timestamp created_at
        timestamp updated_at
    }
    
    DAMAGE_PHOTOS {
        uuid id PK
        uuid application_id FK
        varchar photo_type
        text storage_path
        varchar file_name
        integer file_size
        varchar mime_type
        text description
        uuid uploaded_by FK
        timestamp created_at
    }
    
    REVIEW_RECORDS {
        uuid id PK
        uuid application_id FK
        uuid reviewer_id FK
        varchar reviewer_name
        varchar action
        varchar previous_status
        varchar new_status
        text comments
        text decision_reason
        timestamp inspection_date
        text inspection_notes
        timestamp created_at
    }
    
    DIGITAL_CERTIFICATES {
        uuid id PK
        uuid application_id FK
        varchar certificate_no UK
        text qr_code_data
        text qr_code_image_path
        decimal issued_amount
        uuid issued_by FK
        timestamp issued_at
        boolean is_verified
        timestamp verified_at
        uuid verified_by FK
        boolean is_disbursed
        timestamp disbursed_at
        varchar disbursement_method
        timestamp expires_at
        timestamp created_at
    }
    
    SUBSIDY_ITEMS {
        uuid id PK
        uuid application_id FK
        varchar item_category
        varchar item_name
        text item_description
        integer quantity
        decimal unit_price
        decimal total_price
        boolean approved
        decimal approved_amount
        timestamp created_at
    }
    
    SYSTEM_SETTINGS {
        uuid id PK
        varchar setting_key UK
        text setting_value
        text description
        timestamp updated_at
    }
```

### 資料表關係說明

| 資料表 | 中文名稱 | 關聯 | 說明 |
|--------|----------|------|------|
| `users` | 使用者表 | - | 儲存災民、審核員、管理員資料 |
| `applications` | 申請案件表 | → users | 災民的補助申請案件主表 |
| `damage_photos` | 災損照片表 | → applications, users | 災前/災後/現場勘查照片 |
| `review_records` | 審核記錄表 | → applications, users | 完整的審核歷程記錄 |
| `digital_certificates` | 數位憑證表 | → applications, users | QR Code 數位憑證 |
| `subsidy_items` | 補助項目表 | → applications | 申請的補助項目明細 |
| `system_settings` | 系統設定表 | - | 系統參數設定 |

---

## API 路由架構

### API 端點樹狀圖

```mermaid
graph TB
    Root["根路徑 /"] --> Health["健康檢查 /health"]
    Root --> API["API /api/v1"]
    Root --> Docs["文件 /docs"]
    Root --> Test["測試頁面 /test"]
    
    API --> Users["使用者 /users"]
    API --> Apps["申請案件 /applications"]
    API --> Photos["照片管理 /photos"]
    API --> Reviews["審核管理 /reviews"]
    API --> Certs["數位憑證 /certificates"]
    API --> Stats["統計資料 /stats"]
    
    Users --> UserCreate["POST /users/<br/>建立使用者"]
    Users --> UserGet["GET /users/:id<br/>查詢使用者"]
    Users --> UserGetEmail["GET /users/email/:email<br/>依 Email 查詢"]
    Users --> UserUpdate["PATCH /users/:id<br/>更新使用者"]
    Users --> UserList["GET /users/<br/>列出所有使用者"]
    
    Apps --> AppCreate["POST /applications/<br/>建立申請"]
    Apps --> AppGet["GET /applications/:id<br/>查詢申請"]
    Apps --> AppGetCase["GET /applications/case-no/:no<br/>依案件編號查詢"]
    Apps --> AppGetApplicant["GET /applications/applicant/:id<br/>查詢申請人案件"]
    Apps --> AppUpdate["PATCH /applications/:id<br/>更新申請"]
    Apps --> AppGetStatus["GET /applications/status/:status<br/>依狀態查詢"]
    
    Photos --> PhotoUpload["POST /photos/upload<br/>上傳照片"]
    Photos --> PhotoMultiple["POST /photos/upload-multiple<br/>批次上傳"]
    Photos --> PhotoGet["GET /photos/application/:id<br/>查詢案件照片"]
    Photos --> PhotoDelete["DELETE /photos/:id<br/>刪除照片"]
    Photos --> PhotoInspection["POST /photos/inspection/upload<br/>上傳勘查照片"]
    
    Reviews --> ReviewCreate["POST /reviews/<br/>建立審核記錄"]
    Reviews --> ReviewGet["GET /reviews/application/:id<br/>查詢審核記錄"]
    Reviews --> ReviewApprove["POST /reviews/approve/:id<br/>核准申請"]
    Reviews --> ReviewReject["POST /reviews/reject/:id<br/>駁回申請"]
    
    Certs --> CertCreate["POST /certificates/<br/>建立憑證"]
    Certs --> CertGet["GET /certificates/:no<br/>查詢憑證"]
    Certs --> CertGetApp["GET /certificates/application/:id<br/>查詢案件憑證"]
    Certs --> CertScan["POST /certificates/scan/:no<br/>掃描憑證"]
    Certs --> CertVerify["POST /certificates/gov/verify-qr<br/>政府 API 驗證"]
    Certs --> CertRequest["POST /certificates/gov/create-verification-request<br/>建立驗證請求"]
    
    classDef root fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef group fill:#fff9c4,stroke:#f57f00,stroke-width:2px
    classDef endpoint fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    
    class Root,Health,Docs,Test root
    class API,Users,Apps,Photos,Reviews,Certs,Stats group
    class UserCreate,UserGet,UserGetEmail,UserUpdate,UserList,AppCreate,AppGet,AppGetCase,AppGetApplicant,AppUpdate,AppGetStatus,PhotoUpload,PhotoMultiple,PhotoGet,PhotoDelete,PhotoInspection,ReviewCreate,ReviewGet,ReviewApprove,ReviewReject,CertCreate,CertGet,CertGetApp,CertScan,CertVerify,CertRequest endpoint
```

### API 端點統計

| 路由群組 | 端點數量 | 主要功能 |
|----------|----------|----------|
| 使用者管理 | 5 | 建立、查詢、更新使用者 |
| 申請案件 | 6 | 申請建立、查詢、狀態管理 |
| 照片管理 | 5 | 上傳、查詢、刪除照片 |
| 審核管理 | 4 | 審核記錄、核准、駁回 |
| 數位憑證 | 6 | 憑證發行、驗證、政府 API |
| 統計資料 | 1 | 系統統計資訊 |
| **總計** | **27** | - |

---

## 檔案結構

### 專案目錄樹

```
Mix_Curry/
├── 📄 main.py                    # FastAPI 主應用程式
├── 📄 command.py                 # 資料庫管理工具
├── 📄 requirements.txt           # Python 依賴套件
├── 📄 pyproject.toml            # 專案配置文件
├── 📄 .env                       # 環境變數（需自行建立）
│
├── 📁 app/                       # 應用程式主目錄
│   ├── 📄 settings.py           # 應用程式設定
│   │
│   ├── 📁 models/               # 資料模型
│   │   ├── 📄 models.py        # Pydantic 資料模型
│   │   └── 📄 database.py      # 資料庫服務層
│   │
│   ├── 📁 routers/              # API 路由
│   │   ├── 📄 users.py         # 使用者路由
│   │   ├── 📄 applications.py  # 申請案件路由
│   │   ├── 📄 photos.py        # 照片管理路由
│   │   ├── 📄 reviews.py       # 審核管理路由
│   │   └── 📄 certificates.py  # 數位憑證路由
│   │
│   └── 📁 services/             # 服務層
│       ├── 📄 storage.py       # 檔案儲存服務
│       └── 📄 gov_wallet.py    # 政府憑證服務
│
├── 📁 static/                    # 靜態檔案
│   └── 📄 test_api.html        # 網頁測試介面
│
├── 📁 https/                     # HTTP 測試檔案
│   ├── 📄 test.http            # API 測試集合
│   ├── 📄 README.md            # 測試說明文件
│   ├── 📄 create_test_images.py # 測試圖片生成工具
│   └── 📁 test_images/         # 測試圖片資料夾
│
├── 📁 docs/                      # 文件
│   ├── 📄 README.md            # 專案主文件
│   ├── 📄 FRONTEND_GUIDE.md    # 前端整合指南
│   ├── 📄 QUICKSTART_FRONTEND.md # 前端快速上手
│   ├── 📄 GOV_API_INTEGRATION.md # 政府 API 整合
│   └── 📄 ARCHITECTURE.md      # 系統架構文件（本文件）
│
└── 📄 database_schema.sql       # 資料庫結構 SQL
```

### 分層架構說明

```mermaid
graph TB
    subgraph "Presentation Layer 展示層"
        A1[網頁測試介面]
        A2[REST Client]
        A3[前端應用]
    end
    
    subgraph "API Layer API 層"
        B1[FastAPI Main]
        B2[Routers 路由層]
        B3[Middleware 中介層]
    end
    
    subgraph "Business Logic Layer 業務邏輯層"
        C1[Services 服務層]
        C2[Models 資料模型]
        C3[Validation 驗證]
    end
    
    subgraph "Data Access Layer 資料存取層"
        D1[Database Service]
        D2[Storage Service]
    end
    
    subgraph "Infrastructure Layer 基礎設施層"
        E1[Supabase PostgreSQL]
        E2[Supabase Storage]
        E3[Government API]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    B1 --> B2
    B1 --> B3
    B2 --> C1
    B2 --> C2
    C1 --> C3
    C1 --> D1
    C1 --> D2
    D1 --> E1
    D2 --> E2
    C1 --> E3
    
    classDef layer1 fill:#e3f2fd,stroke:#1976d2
    classDef layer2 fill:#fff3e0,stroke:#f57c00
    classDef layer3 fill:#f3e5f5,stroke:#7b1fa2
    classDef layer4 fill:#e8f5e9,stroke:#388e3c
    classDef layer5 fill:#fce4ec,stroke:#c2185b
    
    class A1,A2,A3 layer1
    class B1,B2,B3 layer2
    class C1,C2,C3 layer3
    class D1,D2 layer4
    class E1,E2,E3 layer5
```

---

## 技術堆疊

### 後端技術棧

```mermaid
graph LR
    subgraph "Web Framework"
        FastAPI[FastAPI 0.109.0]
    end
    
    subgraph "Database & ORM"
        Supabase[Supabase]
        PostgreSQL[PostgreSQL]
        SupabaseClient[Supabase Python Client]
    end
    
    subgraph "Data Validation"
        Pydantic[Pydantic 2.x]
        PydanticSettings[Pydantic Settings]
    end
    
    subgraph "File Storage"
        SupabaseStorage[Supabase Storage]
        QRCode[qrcode + Pillow]
    end
    
    subgraph "HTTP Client"
        HTTPX[HTTPX]
    end
    
    subgraph "Server"
        Uvicorn[Uvicorn]
    end
    
    FastAPI --> Pydantic
    FastAPI --> Uvicorn
    FastAPI --> SupabaseClient
    SupabaseClient --> Supabase
    Supabase --> PostgreSQL
    Supabase --> SupabaseStorage
    FastAPI --> HTTPX
    SupabaseStorage --> QRCode
    
    classDef main fill:#4caf50,stroke:#2e7d32,color:#fff
    classDef db fill:#2196f3,stroke:#1565c0,color:#fff
    classDef util fill:#ff9800,stroke:#e65100,color:#fff
    
    class FastAPI main
    class Supabase,PostgreSQL,SupabaseClient,SupabaseStorage db
    class Pydantic,PydanticSettings,QRCode,HTTPX,Uvicorn util
```

### 前端技術棧

```mermaid
graph LR
    subgraph "測試工具"
        HTML[test_api.html<br/>Vanilla JS]
        REST[REST Client<br/>VS Code Extension]
        HTTP[test.http<br/>HTTP File]
    end
    
    subgraph "建議框架"
        React[React.js]
        Vue[Vue 3]
        Next[Next.js]
    end
    
    subgraph "HTTP 客戶端"
        Fetch[Fetch API]
        Axios[Axios]
    end
    
    HTML --> Fetch
    REST --> HTTP
    React --> Axios
    Vue --> Axios
    Next --> Fetch
    
    classDef test fill:#ffeb3b,stroke:#f57f17
    classDef framework fill:#00bcd4,stroke:#006064,color:#fff
    classDef client fill:#9c27b0,stroke:#4a148c,color:#fff
    
    class HTML,REST,HTTP test
    class React,Vue,Next framework
    class Fetch,Axios client
```

### 外部服務整合

| 服務類型 | 服務名稱 | 用途 | 狀態 |
|----------|----------|------|------|
| 資料庫 | Supabase PostgreSQL | 資料儲存 | ✅ 已整合 |
| 檔案儲存 | Supabase Storage | 照片、QR Code 儲存 | ✅ 已整合 |
| 政府 API | Issuer API | 數位憑證發行 | ✅ 已整合 |
| 政府 API | Verifier API | 憑證驗證 | ✅ 已整合 |
| API 文件 | Swagger UI | 互動式 API 文件 | ✅ 已整合 |
| API 文件 | ReDoc | API 參考文件 | ✅ 已整合 |

---

## 資料流向圖

### 災民申請流程

```mermaid
flowchart TD
    Start([災民開始申請]) --> Register[註冊/登入]
    Register --> FillForm[填寫申請表單]
    FillForm --> UploadPhotos[上傳災損照片]
    UploadPhotos --> Submit[提交申請]
    Submit --> SaveDB[(儲存到資料庫)]
    SaveDB --> Status1{申請狀態}
    
    Status1 -->|pending| WaitReview[等待審核]
    WaitReview --> ReviewerCheck[審核員檢視]
    ReviewerCheck --> Status2{審核結果}
    
    Status2 -->|approved| CreateCert[生成數位憑證]
    Status2 -->|rejected| Reject[駁回通知]
    Status2 -->|need_inspection| Inspection[現場勘查]
    
    Inspection --> UploadInspection[上傳勘查照片]
    UploadInspection --> Status2
    
    CreateCert --> GenQR[生成 QR Code]
    GenQR --> GovAPI{使用政府 API?}
    GovAPI -->|Yes| CallGovAPI[呼叫政府憑證 API]
    GovAPI -->|No| LocalQR[本地生成 QR Code]
    
    CallGovAPI --> SaveCert[(儲存憑證)]
    LocalQR --> SaveCert
    SaveCert --> NotifyVictim[通知災民]
    NotifyVictim --> ScanQR[災民掃描 QR Code]
    ScanQR --> Verify[驗證憑證]
    Verify --> Disburse[發放補助]
    Disburse --> Complete([完成])
    
    Reject --> End([結束])
    
    classDef process fill:#bbdefb,stroke:#1976d2
    classDef decision fill:#fff9c4,stroke:#f57f00
    classDef data fill:#c8e6c9,stroke:#388e3c
    classDef terminal fill:#ffcdd2,stroke:#c62828
    
    class Register,FillForm,UploadPhotos,Submit,ReviewerCheck,CreateCert,GenQR,CallGovAPI,LocalQR,NotifyVictim,ScanQR,Verify,Disburse,UploadInspection,Inspection process
    class Status1,Status2,GovAPI decision
    class SaveDB,SaveCert data
    class Start,Complete,End terminal
```

---

## 安全性架構

### 安全層級

```mermaid
graph TB
    subgraph "Network Layer 網路層"
        A1[HTTPS/TLS]
        A2[CORS Policy]
    end
    
    subgraph "API Layer API 層"
        B1[Request Validation]
        B2[Rate Limiting]
        B3[Input Sanitization]
    end
    
    subgraph "Authentication 身份驗證"
        C1[User Authentication]
        C2[Role-Based Access]
    end
    
    subgraph "Data Layer 資料層"
        D1[Database Access Control]
        D2[Row Level Security RLS]
        D3[Data Encryption]
    end
    
    subgraph "Storage Layer 儲存層"
        E1[Signed URLs]
        E2[Private Buckets]
        E3[File Type Validation]
    end
    
    A1 --> B1
    A2 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> C1
    C1 --> C2
    C2 --> D1
    D1 --> D2
    D2 --> D3
    C2 --> E1
    E1 --> E2
    E2 --> E3
    
    classDef network fill:#e1bee7,stroke:#4a148c
    classDef api fill:#b3e5fc,stroke:#01579b
    classDef auth fill:#c5e1a5,stroke:#33691e
    classDef data fill:#ffccbc,stroke:#bf360c
    classDef storage fill:#f0f4c3,stroke:#827717
    
    class A1,A2 network
    class B1,B2,B3 api
    class C1,C2 auth
    class D1,D2,D3 data
    class E1,E2,E3 storage
```

---

## 效能優化

### 快取策略

```mermaid
graph LR
    Request[用戶請求] --> Cache{快取檢查}
    Cache -->|Hit| Return1[返回快取資料]
    Cache -->|Miss| DB[(查詢資料庫)]
    DB --> Process[處理資料]
    Process --> UpdateCache[更新快取]
    UpdateCache --> Return2[返回資料]
    
    subgraph "快取層級"
        L1[應用層快取<br/>Function Cache]
        L2[資料庫快取<br/>Query Cache]
        L3[CDN 快取<br/>Static Files]
    end
    
    classDef cache fill:#81c784,stroke:#2e7d32
    classDef db fill:#64b5f6,stroke:#1565c0
    
    class Cache,UpdateCache,L1,L2,L3 cache
    class DB db
```

### 索引優化

資料庫已建立的索引：
- ✅ `users.email` - 快速查詢使用者
- ✅ `users.id_number` - 身分證字號查詢
- ✅ `applications.case_no` - 案件編號查詢
- ✅ `applications.applicant_id` - 申請人案件查詢
- ✅ `applications.status` - 狀態過濾查詢
- ✅ `damage_photos.application_id` - 照片關聯查詢
- ✅ `review_records.application_id` - 審核記錄查詢
- ✅ `digital_certificates.certificate_no` - 憑證編號查詢

---

## 部署架構

### 生產環境部署圖

```mermaid
graph TB
    subgraph "用戶端 Client"
        User[使用者瀏覽器]
    end
    
    subgraph "CDN / Load Balancer"
        CDN[CDN / Cloudflare]
        LB[Load Balancer]
    end
    
    subgraph "應用伺服器 Application Servers"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N...]
    end
    
    subgraph "Supabase Cloud"
        DB[(PostgreSQL<br/>主從複製)]
        Storage[Object Storage]
        Auth[Authentication]
    end
    
    subgraph "外部服務 External Services"
        GovAPI[政府數位憑證 API]
        Monitoring[監控服務<br/>Sentry/DataDog]
    end
    
    User --> CDN
    CDN --> LB
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> DB
    API2 --> DB
    API3 --> DB
    
    API1 --> Storage
    API2 --> Storage
    API3 --> Storage
    
    API1 --> GovAPI
    API2 --> GovAPI
    API3 --> GovAPI
    
    API1 --> Monitoring
    API2 --> Monitoring
    API3 --> Monitoring
    
    classDef client fill:#e1f5fe,stroke:#01579b
    classDef cdn fill:#fff3e0,stroke:#e65100
    classDef app fill:#f3e5f5,stroke:#4a148c
    classDef db fill:#e8f5e9,stroke:#2e7d32
    classDef external fill:#fce4ec,stroke:#c2185b
    
    class User client
    class CDN,LB cdn
    class API1,API2,API3 app
    class DB,Storage,Auth db
    class GovAPI,Monitoring external
```

---

## 監控與日誌

### 監控架構

```mermaid
graph TB
    subgraph "應用層監控 Application Monitoring"
        A1[API 請求監控]
        A2[錯誤追蹤]
        A3[效能分析]
    end
    
    subgraph "基礎設施監控 Infrastructure Monitoring"
        B1[伺服器資源監控<br/>CPU/Memory/Disk]
        B2[網路監控]
        B3[可用性監控]
    end
    
    subgraph "業務監控 Business Monitoring"
        C1[申請案件數量]
        C2[審核通過率]
        C3[補助發放統計]
    end
    
    subgraph "日誌系統 Logging System"
        D1[應用日誌]
        D2[存取日誌]
        D3[錯誤日誌]
    end
    
    subgraph "告警系統 Alert System"
        E1[Email 通知]
        E2[Slack 通知]
        E3[SMS 通知]
    end
    
    A1 --> D1
    A2 --> D3
    B1 --> D2
    C1 --> D1
    
    D1 --> E1
    D2 --> E2
    D3 --> E1
    D3 --> E3
    
    classDef app fill:#90caf9,stroke:#1565c0
    classDef infra fill:#a5d6a7,stroke:#2e7d32
    classDef business fill:#ffcc80,stroke:#e65100
    classDef log fill:#ce93d8,stroke:#6a1b9a
    classDef alert fill:#ef9a9a,stroke:#c62828
    
    class A1,A2,A3 app
    class B1,B2,B3 infra
    class C1,C2,C3 business
    class D1,D2,D3 log
    class E1,E2,E3 alert
```

---

## 未來擴展

### 功能擴展計畫

```mermaid
mindmap
  root((災民補助系統))
    現有功能
      使用者管理
      申請案件
      照片上傳
      審核流程
      數位憑證
    
    Phase 1
      行動應用
        iOS App
        Android App
      通知系統
        Email
        SMS
        推播
      
    Phase 2
      進階功能
        多語系支援
        報表系統
        數據分析
      整合服務
        銀行轉帳
        電子支付
        身分驗證
      
    Phase 3
      AI 功能
        智能審核
        照片辨識
        詐欺偵測
      區塊鏈
        不可竄改紀錄
        智能合約
```

---

## 總結

### 系統特色

✅ **模組化設計** - 清晰的分層架構，易於維護和擴展  
✅ **RESTful API** - 標準化的 API 設計，前後端分離  
✅ **完整測試** - 網頁介面、HTTP 檔案、自動化測試  
✅ **政府整合** - 串接政府數位憑證沙盒 API  
✅ **安全可靠** - 多層安全機制，資料加密保護  
✅ **效能優化** - 資料庫索引、快取策略  
✅ **文件完善** - API 文件、架構圖、使用指南  

### 技術亮點

🚀 **FastAPI** - 高效能、自動生成 API 文件  
🗄️ **Supabase** - 開源 Firebase 替代方案  
🔐 **數位憑證** - 政府 API 整合，QR Code 驗證  
📊 **資料完整** - 完整的審核歷程記錄  
🖼️ **檔案管理** - Supabase Storage 整合  

---

**文件版本**: 1.0.0  
**最後更新**: 2025-10-14  
**維護者**: Mix_Curry Development Team

