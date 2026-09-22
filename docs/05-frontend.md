# Frontend Guide

React + TypeScript + Vite. Apple-inspired dark theme, purple accent, pastel statuses.

## Stack

- React 19 · TypeScript
- Vite (dev + build)
- TailwindCSS v4 (utility + a small design-system layer in index.css)
- React Router v7
- TanStack Query v5 (server state)
- Zustand (auth, toasts)
- Axios (API client with JWT refresh)
- Recharts (analytics)
- Leaflet + react-leaflet (maps)

## Folder structure

frontend/src/
  app/
    AppLayout.tsx           admin shell
    DispatcherLayout.tsx    dispatcher shell
    DriverLayout.tsx        driver shell (top nav)
    WarehouseLayout.tsx     warehouse shell
    ProtectedRoute.tsx      requires token
    RoleRedirect.tsx        /home → role-appropriate home
  features/
    landing/                marketing page
    auth/                   Login, Register, AcceptInvite
    analytics/              Dashboard, Analytics
    warehouses/             list
    inventory/              products + stock tabs
    orders/                 list + detail
    deliveries/             list + detail (POD)
    drivers/                list + detail (vehicles, shifts, positions)
    dispatch/               candidates + live map
    routing/                routes + stops + recalc
    notifications/          list + read
    users/                  admin user mgmt + invite modal
    settings/               org + account
    tracking/               public tracking page
    driver/                 DriverHome
    dispatcher/             DispatcherHome
    warehouse/              WarehouseHome
  shared/
    api/                    axios client + auth + users
    components/             Map, Skeleton, StatusBadge, Toaster, TopProgressBar
    hooks/                  useWebSocket
    lib/                    config, status maps
    stores/                 auth, toast

## Routing

All routes are declared in `App.tsx`.
- Public: `/`, `/login`, `/register`, `/invite`, `/track/:token`
- Admin (AppLayout): `/dashboard`, `/analytics`, `/warehouses`, `/inventory`,
  `/orders`, `/orders/:id`, `/deliveries`, `/deliveries/:id`, `/drivers`,
  `/drivers/:id`, `/dispatch`, `/routing`, `/notifications`, `/users`, `/settings`
- Dispatcher (DispatcherLayout): `/dispatcher/*`
- Driver (DriverLayout): `/driver`, `/driver/deliveries/:id`
- Warehouse (WarehouseLayout): `/warehouse/*`
- `/home` redirects by role

`ProtectedRoute` checks `accessToken`. On missing token → redirect to `/login`.

`homePathForRoles(roles)` decides home:
- driver → /driver
- dispatcher → /dispatcher
- warehouse_manager | warehouse_staff → /warehouse
- otherwise → /dashboard

`primaryRole(roles)` picks the highest-priority role from the array (order:
org_admin, warehouse_manager, warehouse_staff, dispatcher, driver).

## State

**Auth (Zustand + persist)** — `shared/stores/auth.ts`
- accessToken, refreshToken, user {id, email, full_name, roles[], organization_id}
- Stored in localStorage under key `auth`
- Read via `useAuthStore()`

**Toasts (Zustand)** — `shared/stores/toast.ts`
- `toast.success(title, desc?)`, `toast.error(...)`, `toast.info(...)`
- Rendered by `<Toaster />` mounted in `main.tsx`

**Server state (React Query)**
- Query keys: `["orders"]`, `["order", id]`, `["deliveries"]`, etc.
- Mutations invalidate the relevant keys.
- No global cache config beyond retry=1, refetchOnWindowFocus=false.

## API client

`shared/api/client.ts`
- Axios instance with `VITE_API_URL`
- Request interceptor attaches `Authorization: Bearer <access>`
- Response interceptor:
  - On 401 → tries refresh (single-flight), retries original request once
  - On any error (except auth endpoints) → fires a toast
- DEV: 500ms artificial latency so skeleton/loading UI is visible

`shared/api/auth.ts`
- `register`, `login`, `fetchMe`

`shared/api/users.ts`
- `listUsers`, `listRoles`, `inviteUser`, `validateInvite`, `acceptInvite`,
  `deactivateUser`, `assignRole`, `revokeRole`

## WebSocket

`shared/hooks/useWebSocket.ts`
- Connects to `WS_URL?token=<jwt>&topics=...`
- Auto-reconnect on unmount, ping every 20s
- Returns `{events, connected}`
- Used in layouts to show Live/Offline dot

## Components

`StatusBadge` — pastel pill with a status dot. Domain-aware via `shared/lib/status.ts`:
- order, delivery, driver, task, assignment, route, org, channel

`Skeleton` — `SkeletonBlock`, `SkeletonText`, `SkeletonCard`, `SkeletonCards`, `SkeletonTable`, `SkeletonPageHeader`

`TopProgressBar` — thin purple gradient bar at the top. Fires on route change and while React Query has fetches/mutations.

`Toaster` — stacked pastel cards, top-right, auto-dismiss.

`Map` — Leaflet wrapper. Dark OSM tiles. Colored circle markers. Optional polylines. Used in Dispatch and public Tracking.

## Theming

All tokens in `src/index.css` under `:root`:
- `--bg`, `--bg-elev`, `--bg-card`, `--border`, `--text`, `--text-dim`, `--text-mute`
- `--accent` (purple 500), `--accent-2` (purple 600), `--accent-glow`
- Pastel status tokens: ok/warn/danger/info/neutral/accent (fg + bg pairs)

Utility classes:
- `.glass` — subtle glass card
- `.glass-hover` — card hover state
- `.btn` `.btn-primary` `.btn-ghost` `.btn-danger`
- `.input`, `.label`
- `.status` + `.status-{kind}` — pill for statuses
- `.table`
- `.skeleton` — shimmer

Status colors (pastel):
- success → #86efac on emerald-400/10
- warning → #fcd34d on amber-400/10
- danger → #fca5a5 on red-400/10
- info → #93c5fd on blue-400/10
- neutral → #d4d4d8 on white/5
- accent → #d8b4fe on purple-400/10

Typography: system font stack (SF Pro / Segoe UI / Inter fallback), letter-spacing -0.01em, no bold heaviness.

## Build & deploy

- Dev: `npm run dev` → http://localhost:5173 (or 5174 if busy)
- Prod build: `npm run build` → `dist/`
- Docker: dev target runs Vite; prod target serves `dist/` via nginx with SPA fallback

## Patterns

- Pages own their queries and mutations.
- Components are pure; they receive props and callbacks.
- Mutations invalidate queries on success.
- Every list page: search input + status filter + skeleton + empty state.
- Every detail page: header with status, timeline, actions, side metadata.
- All status displays use `<StatusBadge domain="..." value="..." />`.

## Extending

Add a page:
1. Create folder `features/<name>/`
2. Component `XxxPage.tsx`
3. Add route in `App.tsx` under the right layout
4. Add nav item in that layout
5. Use existing components (Skeleton, StatusBadge, Map, etc.)
6. `npm run build` before commit