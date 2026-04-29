// Keycloak が返す ID トークンのクレーム型
// oidc-client-ts の IdTokenClaims を拡張する
export interface KeycloakProfile {
  sub: string
  preferred_username: string
  email?: string
  email_verified?: boolean
  given_name?: string
  family_name?: string
  name?: string
  [key: string]: unknown  // その他のクレームを許容
}
