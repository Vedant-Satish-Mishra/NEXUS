# NEXUS design QA checklist

Use at 320, 375, 480, 768, 1024, 1280, and 1440px where supported. Mark each item Pass, Fail, or Not applicable only after inspecting an implemented build.

| Severity | Check |
|---|---|
| Blocker | Login, send, plan approval, tool approval, deletion, and keyboard access work as labelled. |
| Blocker | No cross-user content, misleading success, or unapproved code execution. |
| High | Contrast, focus, heading order, form errors, screen-reader labels, reduced motion, and mobile overflow pass. |
| High | Loading/error/empty/retry states exist for each main flow. |
| Medium | Typography, 4px spacing rhythm, token use, source/run state clarity, and consistent button hierarchy pass. |
| Medium | No console errors, broken assets, clipped content, fake controls, or unreadable tables. |
| Low | Animation timing, hover polish, copy consistency, and screenshot quality are reviewed. |

Review Chrome/Edge or the actual supported browser set once confirmed. Attach evidence for failures and rerun the affected journey after fixes.
