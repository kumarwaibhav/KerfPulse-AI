# Security and threat model

Protected boundaries include browser/session to API, uploaded evidence to inference, model files to loader, MQTT to persistence, and database to exports. Implemented controls include same-origin mutation checks, HttpOnly session cookie, strict schemas, request caps, session-scoped reads and writes, finite-number validation, content hashes and optimistic human review. Source UI renders metadata as text.

Remaining high-priority production controls are maintained OIDC customer identity, organization/site/asset RBAC, scoped device credentials/certificates, TLS and broker topic ACLs, rotation/revocation, artifact approval, encrypted backup and retention. Current Compose broker is private to its network but accepts anonymous clients on that network. Demo session identity is separate from customer identity. Physical connector configuration and user-supplied URLs are disabled, so no new arbitrary network fetch exists.

Threat tests cover cross-session REST/export, stale review versions, conflicting event IDs, malformed/outcome input and oversized requests. Dependency audits and source tests cover their recorded scope; they are not a complete penetration test. No machine-control writes are implemented.

## Threat register

| Severity | Threat and current control | Remaining acceptance |
|---|---|---|
| HIGH | Public demo creates planner sessions; no customer identity | Keep loopback deployment. Add OIDC, named roles and explicit grants before external customer data. |
| HIGH | An internal Compose peer can publish anonymous broker traffic | Device certificates/credentials, topic ACLs, TLS, revocation and negative broker authorization tests. Private network alone is not device identity. |
| HIGH | Client may self-declare publisher provenance | Signed/scoped source identity and commissioning records. Current declared origin is a demo contract, not trusted attestation. |
| HIGH | Small single-machine model may give wrong advice | Human-only review, domain abstention and explicit benchmark labels. Field qualification remains mandatory. |
| MEDIUM | Repeated valid requests consume CPU/storage | Body/batch/session/assessment limits exist. Add deployment-level rate limit, per-source quotas and monitored admission before Internet exposure. |
| MEDIUM | Model or manifest replaced together | Digest detects content mismatch only; approval/signature and restricted artifact write access are needed. |
| MEDIUM | Review races or another session's ID | Owner predicates and optimistic state/version checks; tests cover REST/export isolation and stale updates. Multi-tenant hierarchy remains missing. |
| MEDIUM | Expired demo records mistaken for durable customer archive | Explicit 24-hour session retention; export before expiry. Customer retention/backup/restore policy is separate. |

## Browser and input controls

API sets no-store on API responses, nosniff, same-origin referrer policy and a restrictive same-origin CSP with frame-ancestors none. Mutation middleware rejects cross-site fetches, mismatched origins and non-JSON API content types. Session cookies are HttpOnly and SameSite=Strict, Secure under HTTPS or explicit configuration. Loopback HTTP development is not a public TLS deployment.

React renders labels/findings as escaped text; no new arbitrary HTML renderer or user-controlled network connector is enabled. SQL uses bound values; dynamic table names are an internal fixed allowlist. Finite-number validation rejects NaN/infinity/bool measurements, and forbidden feature/outcome fields cannot enter the model vector. Dependency scans cover known advisories only and do not prove the absence of logic flaws or malicious artifacts.

A complete external release audit must test customer identity/logout/revocation, all tenant/site/asset boundaries, device-to-topic isolation, backup confidentiality and restore, rate/DoS behavior and incident ownership. Those controls are not implied by this local demo's passing tests.
