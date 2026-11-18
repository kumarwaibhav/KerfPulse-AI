# Named identity and operational access

## Implemented boundary

Research replay continues to use the existing demo session. Named operational access uses a separate OIDC authorization-code flow, S256 PKCE, one-use browser-bound state, nonce verification and RS256 ID-token validation. The configured issuer, audience, authorized party, signature, issued-at and expiry are verified. Provider requests are bounded, time-limited, redirect-disabled and restricted to configured provider endpoints. Identity tokens and provider passwords are not stored in browser JavaScript or application sessions.

Application sessions are opaque, hashed server-side, HttpOnly, SameSite=Lax, and Secure for HTTPS. Session validity ends at the earlier of ID-token expiry and eight hours. There is no silent refresh in this stage; sign in again after expiry. Local logout requires CSRF token and invalidates the application session. It does not claim to terminate the provider's separate SSO session. Disabled people and revoked application sessions lose access immediately on the next request.

Successful authentication grants no machine access. Trusted local administration assigns exact organization/site/asset roles. Named source and history APIs recheck grants and never inherit demo workspace permissions. Roles currently define scoped read access; operator/planner/technician write workflows and customer self-service grant administration remain future work. Provider role claims do not grant application privileges.

## UI

Open Operations workspace in the existing application. It shows named account, session expiry, explicit grants, sign-in/out and assigned source health. The source panel separates quality, qualification, freshness, receipts and immutable assessment lineage. With no grants, no machines are visible. With no IdP configured, the UI explains setup instead of pretending to authenticate a user.

## Local provider setup

The optional Keycloak 26.4.7 profile is loopback development integration, not production IdP hosting. It uses start-dev and private local data volume. Production must use maintained TLS/provider/database/backup/MFA/availability policies appropriate to the site.

```powershell
Set-Location E:/pdm_aiiot
pwsh -NoProfile -File scripts/setup-identity.ps1
```

The script generates private administrator credentials in artifacts/private-identity, starts the identity profile and provisions a local-engineer account without machine grants. Read credentials locally from artifacts/private-identity/engineer.json; do not paste them into chat, commit, package or publish them. The administrator credential file controls the local provider, not CNC devices.

Use http://localhost:8000/?workspace=operations for this profile. The app redirects login to its configured canonical origin before creating browser-bound state, preventing localhost/127.0.0.1 callback-cookie mismatch. The API container uses an explicit trusted backchannel origin override to reach identity:8080 while browser/issuer remain localhost:8080. This private HTTP exception is enabled only in local profile; production defaults require HTTPS.

## Access administration

After the person logs in, list identities and assign a role using trusted local terminal access:

```powershell
docker compose exec -T api python -m pdm.identity_admin list
docker compose exec -T api python -m pdm.identity_admin grant --person PERSON_ID --org ORGANIZATION --site SITE --asset ASSET --role operator --actor ADMINISTRATOR_ID
docker compose exec -T api python -m pdm.identity_admin revoke --person PERSON_ID --actor ADMINISTRATOR_ID
```

Scope must exactly match registered device organization/site/asset; no wildcard matching. Revoke removes grants and active application sessions. Commands are local administration, not a replacement for a complete customer administration UI. Audit rows record login/logout and grant/revocation actor references. No source qualification or advisory approval is implicitly granted.

## Generic provider settings

Set PDM_OIDC_ISSUER, PDM_OIDC_CLIENT_ID and PDM_PUBLIC_URL together. Optional PDM_OIDC_CLIENT_SECRET remains server-side. Register exact callback PUBLIC_URL/api/auth/callback, code flow, openid/profile and S256 PKCE. This initial integration requires RS256 and provider endpoints on the configured issuer origin; other algorithms or cross-origin endpoints fail closed until explicitly supported and tested.

PDM_OIDC_ALLOW_LOOPBACK_HTTP=true permits local development only. Optional PDM_OIDC_BACKCHANNEL_URL is a trusted administrator-supplied origin and never comes from requests. TLS remains mandatory outside explicitly configured local exception.

Login attempts are bounded to 20/minute per direct client address and 100 pending browser states globally. Reverse proxies must supply independent ingress throttling and trusted forwarding configuration; this is not Internet-scale DoS protection. Provider tokens are not refreshed or centrally introspected each request. Local revoke/disable and token-bounded session expiry are implemented; provider global/backchannel logout remains pending.

## Source-health corrections

Pending processing, missing required channels, rejected/unsupported model input, changed assessment qualification and quarantined transport conflicts now require attention. Historical assessment remains unchanged; current qualification no longer makes an old result appear current. A valid no-feasible-slot assessment is not mistaken for missing model evidence.

## Verification scope

Signed-token protocol fixtures test PKCE, nonce/state replay, issuer/audience/expiry/iat/authorized-party validation, CSRF logout and failed provider configuration. Independent tests cover disabled accounts, immediate grant removal and foreign discovery endpoints. UI fixtures test scoped account rendering/sign-out; actual provider and browser results are recorded separately in the stage checkpoint. These tests do not prove field utility or physical commissioning.
