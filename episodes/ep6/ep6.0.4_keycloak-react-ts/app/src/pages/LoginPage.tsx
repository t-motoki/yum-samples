import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Container, Typography, Paper } from '@mui/material'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import { userManager } from '../auth/oidcConfig'

export default function LoginPage() {
  const navigate = useNavigate()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState<string | null>(null)

  useEffect(() => {
    userManager.getUser().then((user) => {
      if (user && !user.expired) {
        setIsLoggedIn(true)
        setUsername(user.profile.preferred_username ?? null)
      }
    })
  }, [])

  const handleLogin = () => {
    // リダイレクトに失敗した場合もコンソールに出しておく
    userManager.signinRedirect().catch((err) => {
      console.error('ログインエラー:', err)
    })
  }

  const handleLogout = async () => {
    await userManager.signoutRedirect()
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 10 }}>
      <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
        <LockOutlinedIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Keycloak OIDC デモ
        </Typography>
        {isLoggedIn ? (
          <Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              ログイン中: <strong>{username}</strong>
            </Typography>
            <Button variant="outlined" onClick={() => navigate('/profile')} sx={{ mr: 1 }}>
              プロフィールを見る
            </Button>
            <Button variant="outlined" color="error" onClick={handleLogout}>
              ログアウト
            </Button>
          </Box>
        ) : (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              ログインしていません
            </Typography>
            <Button variant="contained" size="large" onClick={handleLogin}>
              Keycloak でログイン
            </Button>
          </Box>
        )}
      </Paper>
    </Container>
  )
}
