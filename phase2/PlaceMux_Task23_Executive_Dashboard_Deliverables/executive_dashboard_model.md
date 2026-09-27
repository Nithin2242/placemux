# Executive Dashboard Data Model

Sources: student master, application events, company engagement, and platform/MLOps monitoring.

Analytical layers:
1. Executive KPI layer
2. College and placement performance layer
3. Company demand layer
4. Reliability and MLOps layer
5. Validation/control layer

The executive layer consumes governed aggregate outputs rather than exposing unnecessary subject-level fields. Production implementation should apply role-based access, refresh SLAs, certified metric definitions and change control.
