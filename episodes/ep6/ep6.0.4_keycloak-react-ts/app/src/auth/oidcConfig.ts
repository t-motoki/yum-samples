import { UserManager, WebStorageStateStore } from 'oidc-client-ts'

// デモ用にローカル固定。本番では環境変数（import.meta.env.VITE_KEYCLOAK_BASE 等）で管理する
const KEYCLOAK_BASE = 'http://localhost:8080'
const REALM = 'demo'
const CLIENT_ID = 'react-app'

export const userManager = new UserManager({
  authority: `${KEYCLOAK_BASE}/realms/${REALM}`,
  client_id: CLIENT_ID,
  redirect_uri: 'http://localhost:5173/callback',
  post_logout_redirect_uri: 'http://localhost:5173/',
  response_type: 'code',
  scope: 'openid email profile',
  // PKCE は oidc-client-ts がデフォルトで有効
  userStore: new WebStorageStateStore({ store: window.sessionStorage }),
})
