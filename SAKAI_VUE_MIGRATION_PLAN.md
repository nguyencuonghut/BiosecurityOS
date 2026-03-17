# 🎯 Sakai-Vue Frontend Migration Plan

**Scope**: Complete FE redesign using Sakai-Vue template  
**Priority**: Auth → Dashboard → Case pages → Farm/Admin views  
**Timeline**: Flexible, phased approach (4-6 tuần)  
**Current Setup**: Vue 3.5 + Vite 6 + PrimeVue 4.5.4 + Pinia  

---

## 📋 Migration Strategy

### High-Level Phases

```
Phase 0: Setup & Foundation (1 tuần)
├─ Install Sakai-Vue template
├─ Extract & adapt layout components
├─ Setup theme + CSS infrastructure
└─ Create component library wrapper

Phase 1: Auth Foundation (1 tuần)
├─ Migrate LoginView with Sakai layout
├─ Test auth flow
├─ Setup error pages (403, 404)
└─ Validate permissions & token refresh

Phase 2: Dashboard (1-2 tuần)
├─ Migrate ExecutiveDashboard with Sakai layout
├─ Port dashboard widgets/cards
├─ Add charts (ECharts integration)
└─ Test data loading & responsiveness

Phase 3: Core Case Management (2 tuần)
├─ Migrate CaseQueueView (F05.1) → Sakai table + actions
├─ Migrate CaseDetailView (F05.2) → Sakai detail page
├─ Implement RCA tabs & stepper
└─ Test case workflows

Phase 4: Farm/Admin Views (2-3 tuần)
├─ Migrate FarmListView, FarmDetailView
├─ Migrate user management, assessments
├─ Migrate killer metrics, scorecards
└─ Full system validation

Phase 5: Polish & Deploy (1 tuần)
├─ Responsive testing
├─ Performance tuning
├─ Final QA
└─ Production deployment
```

---

## 🔧 Phase 0: Setup & Foundation [WEEK 1]

### Step 0.1: Install Sakai-Vue Template
**Goal**: Get template base, extract layout & component library

```bash
# Option A: Copy from Sakai-Vue repo
cd /tmp
git clone https://github.com/primefaces/sakai-vue.git
cd sakai-vue
npm install

# Option B: Or download ZIP from GitHub
# Then merge into existing project
```

**Deliverable**:
- `/frontend/src/layouts/` → Adapt Sakai layout (AppLayout, AppSidebar, AppTopbar)
- `/frontend/src/components/sakai/` → Reusable Sakai-styled components
- `/frontend/src/styles/sakai/` → Theme + CSS modules from Sakai

### Step 0.2: Extract & Adapt Layout Components
**Files to port from Sakai-Vue**:

| Sakai File | Our Use | Priority |
|-----------|---------|----------|
| `layout/AppLayout.vue` | Main wrapper | HIGH |
| `layout/AppSidebar.vue` | Navigation menu | HIGH |
| `layout/AppTopbar.vue` | Header + user menu | HIGH |
| `layout/AppFooter.vue` | Footer (optional) | LOW |
| `layout/AppMenu.vue` | Menu items logic | HIGH |

**Action**:
1. Copy `layouts/*.vue` from Sakai → our `/frontend/src/layouts/`
2. Keep existing logic: Pinia stores, auth checks, router links
3. Adapt CSS/styling to our design tokens
4. Test navigation flow with existing router

### Step 0.3: Create Sakai Component Wrapper Library
**Goal**: Organize reusable components from Sakai

```
/frontend/src/components/
├── sakai/
│   ├── cards/
│   │   ├── StatCard.vue          (metrics display)
│   │   ├── DataCard.vue          (generic card wrapper)
│   │   └── ChartCard.vue         (chart container)
│   ├── tables/
│   │   ├── FilterableTable.vue   (data table with filter)
│   │   ├── ExpandableTable.vue   (collapsible rows)
│   │   └── ActionTable.vue       (inline actions)
│   ├── forms/
│   │   ├── FormLayout.vue        (grid layout helper)
│   │   ├── FormSection.vue       (form section wrapper)
│   │   └── ActionBar.vue         (save/cancel buttons)
│   ├── modals/
│   │   ├── ConfirmDialog.vue
│   │   └── FormDialog.vue
│   └── layout/
│       ├── PageHeader.vue        (H1 + breadcrumb)
│       ├── PageActions.vue       (top-right buttons)
│       └── ContentPanel.vue      (main content area)
```

### Step 0.4: Theme & CSS Infrastructure
**Action**:
1. Copy Sakai CSS modules → `/frontend/src/styles/sakai/`
2. Keep our design tokens (`variables.css`)
3. Create theme mapping file for customization
4. Update `main.js` to load Sakai CSS

**Files**:
```
/frontend/src/styles/
├── variables.css                 (KEEP: design tokens)
├── sakai/
│   ├── theme.css                 (Sakai main theme)
│   ├── layout.css                (Layout + positioning)
│   ├── components.css            (Component styles)
│   └── responsive.css            (Breakpoints)
├── shared/
│   └── [existing CSS modules]    (KEEP for now)
└── legacy/
    └── [old scoped styles]       (archive)
```

**Output**: ✅ Sakai layout working, navigation functional, theme loaded

---

## 👤 Phase 1: Auth Foundation [WEEK 1-2]

### Step 1.1: Migrate LoginView → Sakai
**Current**: `/frontend/src/views/auth/LoginView.vue`  
**New**: Adapt with Sakai card + form layout

**Changes**:
1. Replace current layout with Sakai centered card
2. Use Sakai form components (Input, Button, Checkbox)
3. Keep existing auth logic (Pinia store, API calls)
4. Add loading state, error messages
5. Test token storage & redirect

**Pattern**:
```vue
<template>
  <div class="login-container sakai-centered">
    <div class="login-card">
      <h1>Biosecurity OS</h1>
      <p>Risk Management System</p>
      <form @submit.prevent="handleLogin">
        <!-- Email input -->
        <!-- Password input -->
        <!-- Remember me checkbox -->
        <!-- Login button (loading state) -->
      </form>
    </div>
  </div>
</template>
```

### Step 1.2: Error Pages (403, 404)
**Files**: `/frontend/src/views/errors/`
- `ForbiddenView.vue` → Sakai error card
- `NotFoundView.vue` → Sakai 404 page
- Add proper styling + back button

### Step 1.3: Test Auth Flow
**Verify**:
- ✅ Login page loads without sidebar
- ✅ Auth credentials accepted
- ✅ Token stored & passed to API
- ✅ Session timeout works
- ✅ Logout redirects to login

**Output**: ✅ Auth flow working with Sakai UI

---

## 📊 Phase 2: Dashboard [WEEK 2-3]

### Step 2.1: ExecutiveDashboard Layout
**Current**: `/frontend/src/views/dashboard/ExecutiveDashboard.vue`  
**New**: Sakai grid layout with responsive cards

**Structure**:
```vue
<template>
  <div class="dashboard-page">
    <!-- Page header -->
    <SakaiPageHeader title="Executive Dashboard" />
    
    <!-- KPI row (4 cards) -->
    <div class="dashboard-grid">
      <SakaiStatCard title="Open Cases" value="24" icon="pi-alert" />
      <SakaiStatCard title="SLA Compliance" value="87%" icon="pi-check" />
      <SakaiStatCard title="Avg Resolution" value="2.4d" icon="pi-clock" />
      <SakaiStatCard title="Risk Score" value="6.2/10" icon="pi-shield" />
    </div>
    
    <!-- Charts section -->
    <div class="dashboard-charts">
      <SakaiChartCard title="Cases by Priority">
        <BarChart :data="priorityData" />
      </SakaiChartCard>
      <SakaiChartCard title="Risk Trends">
        <LineChart :data="trendData" />
      </SakaiChartCard>
    </div>
    
    <!-- Recent cases table -->
    <div class="dashboard-table">
      <SakaiFilterableTable title="Recent Cases" :rows="recentCases" />
    </div>
  </div>
</template>
```

### Step 2.2: Widget Components
**Create Sakai-styled widgets**:
- `SakaiStatCard.vue` → KPI card (number + label + trend)
- `SakaiChartCard.vue` → Chart container
- `SakaiFilterableTable.vue` → Data table with sorting
- `SakaiPageHeader.vue` → Title + breadcrumbs

### Step 2.3: Data Integration
**Keep existing**:
- Pinia `stores/dashboard.js`
- API calls via `services/dashboardService.js`
- ECharts for charts
- Real-time data loading

**Just rewrap in Sakai layout**

### Step 2.4: Testing
- ✅ Dashboard loads with sidebar (app layout)
- ✅ All KPIs display correctly
- ✅ Charts render with real data
- ✅ Responsive on mobile/tablet
- ✅ No layout shifts or styling conflicts

**Output**: ✅ Dashboard with Sakai UI, fully functional

---

## 📋 Phase 3: Core Case Management [WEEK 3-4]

### Step 3.1: CaseQueueView (F05.1)
**Current**: `/frontend/src/views/cases/CaseQueueView.vue` (373 lines)  
**New**: Sakai table layout with filter bar + actions

**Structure**:
```vue
<template>
  <div class="case-queue-page">
    <!-- Page header + actions -->
    <SakaiPageHeader title="Case Review Queue">
      <template #actions>
        <Button label="Create Case" icon="pi-plus" @click="openCreate" />
      </template>
    </SakaiPageHeader>
    
    <!-- Filter bar -->
    <SakaiFilterBar>
      <Select v-model="filters.farm" placeholder="Farm" />
      <Select v-model="filters.priority" placeholder="Priority" />
      <Select v-model="filters.status" placeholder="Status" />
      <Button label="Clear" text />
    </SakaiFilterBar>
    
    <!-- Main table + side preview -->
    <div class="case-queue-container">
      <!-- Sakai table with inline actions -->
      <SakaiActionTable 
        :rows="queueCases" 
        @row-select="selectCase"
        @row-action="openCase"
      >
        <!-- table columns defined -->
      </SakaiActionTable>
      
      <!-- Quick preview panel (sidebar) -->
      <SakaiQuickPreview v-if="selectedCase" :case="selectedCase" />
    </div>
    
    <!-- Create case dialog -->
    <SakaiFormDialog @submit="createCase" />
  </div>
</template>
```

**Key Components**:
- `SakaiPageHeader.vue` → Title + action buttons
- `SakaiFilterBar.vue` → Multi-select filter row
- `SakaiActionTable.vue` → DataTable with row actions
- `SakaiQuickPreview.vue` → Side panel with case details
- `SakaiFormDialog.vue` → Modal form

### Step 3.2: CaseDetailView (F05.2)
**Current**: Large detail page with tabs (Overview, RCA, Timeline)  
**New**: Sakai detail layout with tabbed interface

**Structure**:
```vue
<template>
  <div class="case-detail-page">
    <!-- Header with back button + case number + actions -->
    <SakaiDetailHeader :case="caseDetail" @back="goBack">
      <template #actions>
        <Button label="Edit" icon="pi-pencil" />
        <Button label="Export" icon="pi-download" />
      </template>
    </SakaiDetailHeader>
    
    <!-- Tabbed content -->
    <Tabs>
      <!-- Tab 1: Overview -->
      <TabPanel header="Overview">
        <SakaiDetailSection>
          <!-- Case info cards -->
        </SakaiDetailSection>
      </TabPanel>
      
      <!-- Tab 2: RCA (Root Cause Analysis) -->
      <TabPanel header="RCA">
        <SakaiRCAPanel :case="caseDetail" />
      </TabPanel>
      
      <!-- Tab 3: Timeline -->
      <TabPanel header="Timeline">
        <SakaiTimeline :events="caseTimeline" />
      </TabPanel>
    </Tabs>
  </div>
</template>
```

### Step 3.3: Specialized Components
- `SakaiDetailHeader.vue` → Back + title + actions
- `SakaiDetailSection.vue` → Info group with labels
- `SakaiRCAPanel.vue` → RCA editor (factors, causes, actions)
- `SakaiTimeline.vue` → Event timeline with icons
- `SakaiStatusStepper.vue` → Case status pipeline

### Step 3.4: Data & Logic
**Keep existing**:
- `stores/riskCase.js` (Pinia)
- `services/caseService.js` (API)
- Form validation
- Permissions checks

**Test workflow**:
- ✅ Queue view filters & pagination
- ✅ Case detail loads all tabs
- ✅ RCA editing works
- ✅ Create case dialog submits
- ✅ Timeline displays events
- ✅ Responsive on mobile

**Output**: ✅ Case management fully redesigned

---

## 🌾 Phase 4: Farm/Admin Views [WEEK 4-5]

### Step 4.1: FarmListView → Sakai
**Apply same pattern as CaseQueue**:
- Page header with actions
- Filter bar (region, risk level, status)
- Searchable table with inline actions
- Side preview panel
- Create/Edit dialogs

### Step 4.2: FarmDetailView → Sakai
**Tabbed layout**:
- Tab 1: Farm Info (ID, location, contact, metadata)
- Tab 2: Areas (nested list with inline edit)
- Tab 3: Routes (risk point tracking)
- Tab 4: Risk Points (threat assessment)
- Tab 5: Assessments (audit history)

### Step 4.3: User Management
**Admin pages**:
- UserListView → Sakai table + filter
- Roles & permissions pages
- Audit logs

### Step 4.4: Assessment & Scorecard Pages
**Similar pattern**:
- List views with filters
- Detail editors with forms
- Charts & embedded analytics

### Step 4.5: Killer Metrics Pages
- Definition admin interface
- Event logging
- Trend analysis

**Output**: ✅ All major views redesigned with Sakai

---

## ✅ Phase 5: Polish & Deploy [WEEK 5-6]

### Step 5.1: Responsive Testing
- Test all pages on:
  - Desktop (1920x1080, 1366x768)
  - Tablet (iPad 768x1024)
  - Mobile (iPhone 375x667)
- Fix layout shifts, font sizing, spacing

### Step 5.2: Performance Tuning
- Code split large views
- Lazy load images
- Optimize bundle size
- Check lighthouse scores

### Step 5.3: Final QA
- Full feature testing
- API integration validation
- Auth/permissions on all pages
- Dark mode testing (if supported)
- Cross-browser testing (Chrome, Firefox, Safari)

### Step 5.4: Deployment
- Build & deploy to staging
- Final smoke tests
- Deploy to production
- Monitor error logs

**Output**: ✅ Production-ready Sakai-Vue FE

---

## 📊 Detailed Task Breakdown

### Phase 0 Tasks (Find & bookmark Sakai components)
```
☐ 0.1.1 - Clone Sakai-Vue repo, explore structure
☐ 0.1.2 - Document layout file list (navbar, sidebar, footer patterns)
☐ 0.2.1 - Copy AppLayout.vue → adapt for our routes
☐ 0.2.2 - Copy AppSidebar.vue → integrate with our menu data
☐ 0.2.3 - Copy AppTopbar.vue → keep user + logout logic
☐ 0.3.1 - Create `/components/sakai/` directory
☐ 0.3.2 - Create wrapper components (cards, tables, forms)
☐ 0.4.1 - Copy Sakai CSS → `/styles/sakai/`
☐ 0.4.2 - Update main.js with Sakai theme
☐ 0.4.3 - Test: No styling conflicts with existing Pinia stores
```

### Phase 1 Tasks (Auth with Sakai)
```
☐ 1.1.1 - Adapt LoginView with Sakai centered card
☐ 1.1.2 - Test login flow (token, redirect, session)
☐ 1.2.1 - Migrate ForbiddenView.vue (403 page)
☐ 1.2.2 - Migrate NotFoundView.vue (404 page)
☐ 1.3.1 - Full auth flow QA
```

### Phase 2 Tasks (Dashboard with Sakai)
```
☐ 2.1.1 - Create SakaiStatCard.vue
☐ 2.1.2 - Create SakaiChartCard.vue
☐ 2.2.1 - Migrate ExecutiveDashboard → Sakai grid + cards
☐ 2.3.1 - Keep data loading, just rewrap layout
☐ 2.4.1 - Test dashboard on desktop, tablet, mobile
```

### Phase 3 Tasks (Case Management)
```
☐ 3.1.1 - Create SakaiPageHeader.vue
☐ 3.1.2 - Create SakaiFilterBar.vue
☐ 3.1.3 - Create SakaiActionTable.vue
☐ 3.1.4 - Migrate CaseQueueView → Sakai layout
☐ 3.1.5 - Migrate CaseDetailView → Sakai tabs
☐ 3.2.1 - Create SakaiQuickPreview.vue
☐ 3.2.2 - Create SakaiFormDialog.vue
☐ 3.3.1 - Full case workflow testing
```

### Phase 4 Tasks (Farm/Admin)
```
☐ 4.1.1 - Migrate FarmListView → Sakai
☐ 4.1.2 - Migrate FarmDetailView → Sakai tabs
☐ 4.2.1 - Migrate admin pages (users, roles)
☐ 4.3.1 - Migrate assessment pages
☐ 4.4.1 - Migrate killer metric pages
```

### Phase 5 Tasks (QA & Deploy)
```
☐ 5.1.1 - Responsive testing (3 breakpoints)
☐ 5.2.1 - Performance tuning (bundle size, lighthouse)
☐ 5.3.1 - Full system QA + bug fixes
☐ 5.4.1 - Deploy to staging + tests
☐ 5.4.2 - Deploy to production
```

---

## 🎨 Design Principles (from Sakai-Vue)

1. **Consistency**: Same colors, spacing, typography across pages
2. **Responsiveness**: Mobile-first approach, all views scale properly
3. **Component Reuse**: DRY principle - shared cards, tables, forms
4. **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation
5. **Performance**: Lazy loading, code splitting, optimized assets

---

## 🛠️ Tech Stack (No Changes to Existing Foundation)

| Layer | Tech | Status |
|-------|------|--------|
| **UI Framework** | Vue 3.5 | ✅ Keep |
| **Bundler** | Vite 6 | ✅ Keep |
| **Component Lib** | PrimeVue 4.5.4 | ✅ Keep |
| **State Mgmt** | Pinia | ✅ Keep |
| **API Client** | Axios | ✅ Keep |
| **Routing** | Vue Router 4.4 | ✅ Keep |
| **Charts** | ECharts + vue-echarts | ✅ Keep |
| **Sakai Template** | Sakai-Vue (ref) | 🆕 Add |

---

## ⏱️ Estimated Timeline

| Phase | Duration | Key Deliverable |
|-------|----------|------------------|
| Phase 0 | 1 week | Sakai layout working + components |
| Phase 1 | 1 week | Auth flow with Sakai UI |
| Phase 2 | 1-2 weeks | Dashboard fully redesigned |
| Phase 3 | 2 weeks | Case management complete |
| Phase 4 | 2-3 weeks | Farm/Admin views migrated |
| Phase 5 | 1 week | QA, testing, deployment |
| **Total** | **4-6 weeks** | **Production-ready Sakai-Vue FE** |

---

## 💡 Next Steps (Immediate)

1. ✅ **Approved**: Full Sakai-Vue redesign
2. 🎯 **Start Phase 0**: Begin this week
3. 📦 **Step 1**: Install Sakai-Vue template, explore layout files
4. 🔄 **Step 2**: Create initial layout components
5. ✨ **Step 3**: Begin LoginView migration

**Ready to start?** → Let's begin Phase 0, Step 1 (Setup & Foundation)
