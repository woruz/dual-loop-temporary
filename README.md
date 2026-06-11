app/
├── core/           ← Business logic (no external dependencies)
│   ├── entities/   ← Domain models
│   ├── ports/      ← Abstract interfaces (contracts)
│   └── use_cases/  ← Application logic / orchestration
│
├── infrastructure/ ← Concrete implementations of ports
│   └── adapters/
│
└── server/         ← Delivery layer (HTTP + async workers)
    ├── routers/
    └── workers/




app/
├── core/
│   ├── entities/
│   │   └── auth.py          ← NEW: User, Session, OAuthProfile entities
│   ├── ports/
│   │   ├── auth_repo.py     ← NEW: abstract persistence for credentials/sessions
│   │   └── oauth_port.py    ← NEW: abstract OAuth provider contract
│   └── use_cases/
│       ├── register_user.py ← NEW
│       ├── login_user.py    ← NEW
│       └── oauth_login.py   ← NEW
│
├── infrastructure/adapters/
│   ├── postgres_auth_repo.py  ← NEW: implements auth_repo
│   └── google_oauth.py        ← NEW: implements oauth_port (Google/GitHub etc.)
│
└── server/
    ├── routers/
    │   └── auth.py            ← NEW: /auth/* endpoints
    └── dependencies.py        ← EDIT: add get_current_user dep 











for checking status > git status 
for fetch and push -> git remote -v 
for addin it -> git add .
for commiting it into the repo -> git commit -m "O auth depend"
for push origin main -> git push --ser-upstream origin
deature_Oauth 

for testing i will use pytest tests/unit/
