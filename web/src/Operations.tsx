import { useEffect, useState } from 'react';
import { SourceHealth } from './SourceHealth';

type Identity = { configured: boolean; authenticated: boolean; person: null | { id: string; display_name: string; csrf: string; expires_at: string;
  grants: { org_id: string; site_id: string; asset_id: string; role: string }[] } };

export function Operations() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function refresh() {
    try {
      const response = await fetch('/api/auth/me');
      if (!response.ok) throw new Error('Identity service unavailable. Retry after service recovery.');
      setIdentity(await response.json()); setError('');
    } catch (e) { setError(String(e)); }
  }
  useEffect(() => { void refresh(); const interval = window.setInterval(() => void refresh(), 30000); return () => window.clearInterval(interval); }, []);
  async function logout() {
    try {
      const response = await fetch('/api/auth/logout', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': identity?.person?.csrf ?? '' }, body: '{}' });
      if (!response.ok) throw new Error('Sign-out failed. Retry.');
      setIdentity(null); setMessage('Application signed out. On shared devices, also sign out of your identity provider.'); await refresh();
    } catch (e) { setError(String(e)); }
  }
  return <section className="fresh-workspace operations-workspace">
    <section className="panel" style={{ padding: 24, marginBottom: 20 }}>
      <span className="eyebrow">NAMED ACCESS · ASSIGNED MACHINES</span><h2>Operations workspace</h2>
      <p>Sign in through your organization’s identity provider. Machine access follows explicit organization, site and asset grants.</p>
      {error && <p role="alert">{error} Access status may be outdated.</p>}
      {message && <p role="status">{message}</p>}
      {!identity && !error && <p role="status">Checking sign-in…</p>}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', margin: '16px 0' }}>
        <button className="button secondary" onClick={() => void refresh()}>Refresh account</button>
        {identity?.configured && !identity.authenticated && <a className="button primary" href="/api/auth/login">Sign in with organization</a>}
        {identity?.authenticated && <button className="button secondary" onClick={() => void logout()}>Sign out of application</button>}
      </div>
      {identity && !identity.configured && <p>Organization login is not configured. Local administrator must connect an OIDC provider before named-user login is available. Research replay remains available separately.</p>}
      {identity?.person && <><h3>{identity.person.display_name}</h3><p>Session expires {identity.person.expires_at}.</p>
        <details><summary>Account identifier for access administration</summary><code style={{ overflowWrap: 'anywhere' }}>{identity.person.id}</code><p>Administrator assigns roles to exact machine scopes. Signing in alone does not grant access.</p></details>
        {!identity.person.grants.length ? <p>No machine grants assigned. Contact local administrator.</p> : <ul>{identity.person.grants.map(g => <li key={[g.org_id,g.site_id,g.asset_id,g.role].join('/')}>{g.org_id} / {g.site_id} / {g.asset_id} · {g.role}</li>)}</ul>}
      </>}
    </section>
    {identity?.authenticated && !error && <SourceHealth endpoint="/api/operations/sources" named />}
  </section>;
}
