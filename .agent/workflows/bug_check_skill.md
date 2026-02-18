---
description: Comprehensive self-verification workflow to detect and fix bugs before user delivery.
---

# Bug-Check Skill Workflow

Follow these steps rigorously before calling `notify_user` or finishing a task.

// turbo-all
## 1. Static Analysis & Linting
Run the following commands to ensure no syntax errors or linting violations:
```bash
cd frontend
npm run lint
```
(Repeat for backend if applicable)

## 2. Build Verification
Ensure the application compiles correctly in production mode:
```bash
cd frontend
npm run build
```

## 3. Visual & Functional Audit
- [ ] **Contrast Check**: Verify all text is readable against its background (WCAG AA standard).
- [ ] **Responsiveness**: Check layout at different screen widths.
- [ ] **State Consistency**: Ensure UI updates correctly after state changes (e.g., zoom, toggle).

## 4. Logic & API Sanity
- [ ] Verify API endpoints return expected status codes (200/201).
- [ ] Check console for any runtime errors or warnings.

## 5. Metadata & Summary Review
- [ ] Ensure `task.md` is fully updated.
- [ ] Ensure `walkthrough.md` contains screenshots or proof of work if applicable.
