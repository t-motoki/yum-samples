import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Container } from '@mui/material'
import { userManager } from '../auth/oidcConfig'
import type { KeycloakProfile } from '../auth/types'
import ProfileCard from '../components/ProfileCard'

export default function ProfilePage() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState<KeycloakProfile | null>(null)

  useEffect(() => {
    userManager.getUser().then((user) => {
      if (!user || user.expired) {
        navigate('/')
        return
      }
      // user.profile は IdTokenClaims 型。KeycloakProfile にキャストして扱う
      setProfile(user.profile as KeycloakProfile)
    })
  }, [navigate])

  const handleLogout = async () => {
    await userManager.signoutRedirect()
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <ProfileCard profile={profile} onLogout={handleLogout} />
    </Container>
  )
}
